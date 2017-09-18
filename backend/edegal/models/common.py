from django.core.validators import RegexValidator


validate_slug = RegexValidator(
    regex=r'[a-z0-9-]+',
    message='Tekninen nimi saa sisältää vain pieniä kirjaimia, numeroita sekä väliviivoja.'
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
        blank=True,  # actually not, but autogenerated anyway
        max_length=63,
        validators=[validate_slug],
        verbose_name='Tekninen nimi',
        help_text=(
            'Tekninen nimi eli "slug" näkyy URL-osoitteissa. Sallittuja '
            'merkkejä ovat pienet kirjaimet, numerot ja väliviiva. Jos jätät teknisen nimen tyhjäksi, '
            'se generoidaan automaattisesti otsikosta. Jos muutat teknistä nimeä julkaisun jälkeen, '
            'muista luoda tarvittavat uudelleenohjaukset.'
        ),
    )

    title = dict(
        max_length=1023,
        verbose_name='Otsikko',
        help_text='Otsikko näytetään automaattisesti sivun ylälaidassa sekä valikossa.',
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
        help_text=(
            'Saman yläsivun alaiset sivut järjestetään valikossa tämän luvun mukaan nousevaan '
            'järjestykseen (pienin ensin).'
        )
    )

    is_public = dict(
        default=True,
        verbose_name=u'Julkinen',
        help_text=u'Ei-julkiset albumit näkyvät vain ylläpitokäyttäjille.',
    )
