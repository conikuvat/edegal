import logging
import shutil
from contextlib import contextmanager
from os import makedirs
from os.path import dirname

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from mptt.models import MPTTModel, TreeForeignKey
from PIL import Image

from .utils import slugify, pick_attrs, log_get_or_create


logger = logging.getLogger(__name__)

validate_slug = RegexValidator(
    regex=r'[a-z0-9-]+',
    message= 'Tekninen nimi saa sisältää vain pieniä kirjaimia, numeroita sekä väliviivoja.'
)

validate_path = RegexValidator(
    regex=r'[a-z0-9-/]+',
    message='Polku saa sisältää vain pieniä kirjaimia, numeroita, väliviivoja sekä kauttaviivoja.'
)


class CommonFields(object):
    path = dict(
        max_length=1023,
        validators=[validate_path],
        verbose_name='Polku',
        help_text='Polku määritetään automaattisesti teknisen nimen perusteella.',
        unique=True,
    )

    slug = dict(
        blank=True, # actually not, but autogenerated anyway
        max_length=63,
        validators=[validate_slug],
        verbose_name='Tekninen nimi',
        help_text='Tekninen nimi eli "slug" näkyy URL-osoitteissa. Sallittuja '
            'merkkejä ovat pienet kirjaimet, numerot ja väliviiva. Jos jätät teknisen nimen tyhjäksi, '
            'se generoidaan automaattisesti otsikosta. Jos muutat teknistä nimeä julkaisun jälkeen, '
            'muista luoda tarvittavat uudelleenojaukset.',
    )

    title = dict(
        max_length=1023,
        verbose_name='Otsikko',
        help_text='Otsikko näytetään automaattisesti sivun ylälaidassa sekä valikossa. Älä lisää erillistä pääotsikkoa sivun tekstiin.',
    )

    description = dict(
        verbose_name='Kuvaus',
        help_text='Näkyy mm. hakukoneille sekä RSS-asiakasohjelmille.',
        blank=True,
        default='',
    )

    order = dict(
        default=0,
        verbose_name='Järjestys',
        help_text='Saman yläsivun alaiset sivut järjestetään valikossa tämän luvun mukaan nousevaan '
            'järjestykseen (pienin ensin).'
    )


class Album(MPTTModel):
    slug = models.CharField(**CommonFields.slug)
    parent = TreeForeignKey('self',
        null=True,
        blank=True,
        related_name='subalbums',
        db_index=True,
        verbose_name='Yläalbumi',
        help_text='Tämä albumi luodaan valitun albumin alaisuuteen. Juurialbumilla ei ole yläalbumia.'
    )
    path = models.CharField(**CommonFields.path)

    title = models.CharField(**CommonFields.title)
    description = models.TextField(**CommonFields.description)

    cover_picture = models.ForeignKey('Picture', null=True, blank=True, related_name='+')

    is_public = models.BooleanField(
        default=True,
        verbose_name=u'Julkinen',
        help_text=u'Ei-julkiset albumit näkyvät vain ylläpitokäyttäjille.',
    )

    def as_dict(self):
        return pick_attrs(self,
            'slug',
            'path',
            'title',
            'description',

            breadcrumb=[ancestor._make_breadcrumb() for ancestor in self.get_ancestors()],
            subalbums=[subalbum._make_subalbum() for subalbum in self.subalbums.all()],
            pictures=[picture.as_dict() for picture in self.pictures.all()],
            thumbnail=self._make_thumbnail(),
        )

    def _make_thumbnail(self):
        if self.cover_picture:
            return self.cover_picture.get_thumbnail().as_dict()
        else:
            return None

    def _make_breadcrumb(self):
        return pick_attrs(self,
            'path',
            'title',
        )

    def _make_subalbum(self):
        return pick_attrs(self,
            'path',
            'title',
            thumbnail=self._make_thumbnail(),
        )

    def _make_path(self):
        if self.parent is None:
            return '/'
        else:
            # XX ugly
            pth = self.parent.path + '/' + self.slug
            if pth.startswith('//'):
                pth = pth[1:]
            return pth

    def _select_cover_picture(self):
        first_subalbum = self.subalbums.filter(cover_picture__isnull=False).first()
        if first_subalbum is not None:
            return first_subalbum.cover_picture

        first_picture = self.pictures.first()
        if first_picture is not None:
            return first_picture

        return None

    def save(self, *args, **kwargs):
        traverse = kwargs.pop('traverse', True)

        if self.title and not self.slug:
            if self.parent:
                self.slug = slugify(self.title)
            else:
                self.slug = '-root-album'

        if self.slug:
            self.path = self._make_path()

        if self.cover_picture is None:
            self.cover_picture = self._select_cover_picture()

        return_value = super(Album, self).save(*args, **kwargs)

        # In case path changed, update child pictures' paths.
        for picture in self.pictures.all():
            picture.save()

        # In case thumbnails or path changed, update whole family with updated information.
        if traverse:
            for album in self.get_family():

                # Cannot use identity or id because self might not be saved yet!
                if album.path != self.path:
                    logger.debug('Album.save(traverse=True) visiting {path}'.format(path=album.path))
                    album.save(traverse=False)

    @classmethod
    def get_album_by_path(cls, path, **extra_criteria):
        q = Q(path=path) | Q(pictures__path=path)

        if extra_criteria:
            q &= Q(**extra_criteria)

        # FIXME In SQLite, this does a full table scan on gallery_album when the WHERE over the JOIN gallery_picture
        # is present. Need to check if this is the case on PostgreSQL, too.
        return (cls.objects.distinct()
            .select_related('cover_picture')
            .prefetch_related('cover_picture__media')
            .prefetch_related('pictures')
            .prefetch_related('pictures__media')
            .prefetch_related('pictures__media__spec')
            .prefetch_related('subalbums')
            .prefetch_related('subalbums__cover_picture')
            .get(q)
        )

    def __str__ (self):
        return self.path

    class Meta:
        verbose_name = 'Albumi'
        verbose_name_plural = 'Albumit'
        unique_together = [('parent', 'slug')]


class Picture(models.Model):
    slug = models.CharField(**CommonFields.slug)
    album = models.ForeignKey(Album, related_name='pictures')
    order = models.IntegerField(**CommonFields.order)
    path = models.CharField(**CommonFields.path)

    title = models.CharField(**CommonFields.title)
    description = models.TextField(**CommonFields.description)

    def as_dict(self):
        return pick_attrs(self,
            'path',
            'title',
            'description',
            media=[medium.as_dict() for medium in self.media.all()],
            thumbnail=self.get_thumbnail().as_dict(),
        )

    def _make_path(self):
        assert self.album
        return self.album.path + '/' + self.slug

    def get_original(self):
        return self.media.get(spec=None)

    def get_thumbnail(self):
        return self.media.get(spec__is_default_thumbnail=True)

    def save(self, *args, **kwargs):
        if self.title and not self.slug:
            self.slug = slugify(self.title)

        if self.slug:
            self.path = self._make_path()

        return super(Picture, self).save(*args, **kwargs)

    def __str__ (self):
        return self.path

    class Meta:
        verbose_name = 'Kuva'
        verbose_name_plural = 'Kuvat'
        unique_together = [('album', 'slug')]
        ordering = ('album', 'order')


class MediaSpec(models.Model):
    max_width = models.PositiveIntegerField()
    max_height = models.PositiveIntegerField()
    quality = models.PositiveIntegerField()

    is_default_thumbnail = models.BooleanField(default=False)

    @property
    def size(self):
        return self.max_width, self.max_height

    def __str__(self):
        return "{width}x{height}q{quality}".format(
            width=self.max_width,
            height=self.max_height,
            quality=self.quality,
        )


class Media(models.Model):
    picture = models.ForeignKey(Picture, related_name='media')
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    src = models.ImageField(
        null=True,
        max_length=255,
        width_field='width',
        height_field='height',
    )
    spec = models.ForeignKey(MediaSpec, null=True, blank=True)

    def as_dict(self):
        return pick_attrs(self,
            'width',
            'height',
            src=self.src.url,
            original=self.is_original,
        )

    @property
    def is_original(self):
        return self.spec is None

    @property
    def path(self):
        return self.src

    def get_canonical_path(self, prefix=settings.MEDIA_ROOT + '/'):
        """
        Returns the canonical path of this medium. This is where the file would be stored
        unless in-place mode was used.

        Originals: /media/pictures/path/to/album/mypicture.jpg
        Previews: /media/previews/path/to/album/mypicture/640x480q60.jpg
        """
        if self.is_original:
            base_dir = 'pictures'
            postfix = ''
        else:
            base_dir = 'previews'
            postfix = '/' + str(self.spec)

        # TODO hardcoded jpeg
        return "{prefix}{base_dir}{path}{postfix}.jpg".format(
            prefix=prefix,
            base_dir=base_dir,
            path=self.picture.path,
            postfix=postfix,
        )

    def get_absolute_uri(self):
        return self.src.url

    def get_absolute_fs_path(self):
        return self.src.path

    @contextmanager
    def as_image(self):
        image = Image.open(self.src.path)
        try:
            yield image
        finally:
            image.close()

    @classmethod
    def import_local_media(cls, picture, input_filename, mode='inplace', media_specs=None):
        if media_specs is None:
            media_specs = MediaSpec.objects.all()

        original_media, unused = cls.get_or_create_original_media(picture, input_filename, mode)

        for spec in media_specs:
            cls.get_or_create_scaled_media(original_media, spec)

    @classmethod
    def make_absolute_path_media_relative(cls, original_path):
        assert original_path.startswith(settings.MEDIA_ROOT)

        # make path relative to /media/
        original_path = original_path[len(settings.MEDIA_ROOT):]

        # remove leading slash
        if original_path.startswith('/'):
            original_path = original_path[1:]

        return original_path

    @classmethod
    def process_file_location(cls, original_media, input_filename, mode='inplace'):
        if mode == 'inplace':
            original_path = abspath(input_filename)
        elif mode in ('copy', 'move'):
            original_path = original_media.get_canonical_path()
            makedirs(dirname(original_path), exist_ok=True)

            if mode == 'copy':
                shutil.copyfile(input_filename, original_path)
            elif mode == 'move':
                shutil.move(input_filename, original_path)
            else:
                raise NotImplementedError(mode)
        else:
            raise NotImplementedError(mode)

        return cls.make_absolute_path_media_relative(original_path)

    @classmethod
    def get_or_create_original_media(cls, picture, input_filename, mode='inplace'):
        media, created = Media.objects.get_or_create(
            picture=picture,
            spec=None,
        )

        log_get_or_create(logger, media, created)

        src_missing = not media.src
        if src_missing:
            media.src = cls.process_file_location(media, input_filename, mode)
            media.save()

        log_get_or_create(logger, media.src, src_missing)

        return media, created

    @classmethod
    def get_or_create_scaled_media(cls, original_media, spec):
        assert original_media.is_original

        scaled_media, created = Media.objects.get_or_create(
            picture=original_media.picture,
            spec=spec,
        )

        log_get_or_create(logger, scaled_media, created)

        src_missing = not scaled_media.src
        if src_missing:
            makedirs(dirname(scaled_media.get_canonical_path()), exist_ok=True)
            with original_media.as_image() as image:
                image.thumbnail(spec.size)
                image.save(scaled_media.get_canonical_path(), 'JPEG', quality=scaled_media.spec.quality)

            scaled_media.src = scaled_media.get_canonical_path('')
            scaled_media.save()

        log_get_or_create(logger, scaled_media.src, src_missing)

        return scaled_media, created

    def __str__(self):
        return self.src.url if self.src else self.get_canonical_path('')

    class Meta:
        verbose_name = 'Media'
        verbose_name_plural = 'Media'
