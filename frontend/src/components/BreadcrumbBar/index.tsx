import React from 'react';

import Button from 'react-bootstrap/Button';
import Container from 'react-bootstrap/Container';
import { LinkContainer } from 'react-router-bootstrap';
import { Link } from 'react-router-dom';
import editorIcons from 'material-design-icons/sprites/svg-sprite/svg-sprite-editor-symbol.svg';
import socialIcons from 'material-design-icons/sprites/svg-sprite/svg-sprite-social-symbol.svg';

import { getCached } from '../../helpers/getAlbum';
import Album from '../../models/Album';
import Breadcrumb from '../../models/Breadcrumb';
import { T, TranslationFunction } from '../../translations';
import DownloadDialog, { useDownloadDialogState } from '../DownloadDialog';

import './index.scss';

const breadcrumbSeparator = ' » ';

function getBreadcrumbTitle(breadcrumb: Breadcrumb, t: TranslationFunction<{ photographers: string; timeline: string }>) {
  if (breadcrumb.path === '/photographers') {
    return t(r => r.photographers);
  } else if (breadcrumb.path.endsWith('/timeline')) {
    return t(r => r.timeline);
  } else {
    return breadcrumb.title;
  }
}

const downloadAlbumPollingDelay = 3000;

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function BreadcrumbBar({ album }: { album: Album }): JSX.Element {
  const t = React.useMemo(() => T(r => r.BreadcrumbBar), []);
  const { path, title, breadcrumb } = album;
  const fullBreadcrumb = React.useMemo(() => breadcrumb.slice(1).concat([{ path, title }]), [breadcrumb, path, title]);
  const canDownload = album.is_downloadable && album.pictures.length;

  const [isDownloadPreparing, setDownloadPreparing] = React.useState(false);
  const { isDownloadDialogOpen, openDownloadDialog, closeDownloadDialog } = useDownloadDialogState();

  const downloadAlbum = React.useCallback(async () => {
    let downloadableAlbum = album;
    if (!album.download_url) {
      // Zip not yet created
      setDownloadPreparing(true);

      // Trigger zip creation
      downloadableAlbum = await getCached(album.path, 'jpeg', true, true);

      // Poll for zip creation to finish
      while (!downloadableAlbum.download_url) {
        await sleep(downloadAlbumPollingDelay);
        downloadableAlbum = await getCached(album.path, 'jpeg', true);
      }
    }

    setDownloadPreparing(false);
    window.location.href = downloadableAlbum.download_url;
  }, [album]);

  React.useEffect(() => {
    document.title = fullBreadcrumb.map(crumb => getBreadcrumbTitle(crumb, t)).join(breadcrumbSeparator);
  }, [fullBreadcrumb, t]);

  return (
    <Container fluid className="BreadcrumbBar d-flex flex-column flex-sm-row justify-content-between">
      <nav className="BreadcrumbBar-breadcrumb">
        {fullBreadcrumb.map((item, index) => {
          const isActive = index === fullBreadcrumb.length - 1;
          const content = getBreadcrumbTitle(item, t);
          const separator = index > 0 ? breadcrumbSeparator : '';
          if (isActive) {
            return (
              <React.Fragment key={item.path}>
                {separator} {content}
              </React.Fragment>
            );
          } else {
            return (
              <React.Fragment key={item.path}>
                {separator}
                <Link key={item.path} to={item.path}>
                  {content}
                </Link>
              </React.Fragment>
            );
          }
        })}
      </nav>
      <nav className="BreadcrumbBar-actions">
        {canDownload ? (
          <Button variant="link" size="sm" onClick={openDownloadDialog}>
            <svg className="BreadcrumbBar-icon">
              <use xlinkHref={`${editorIcons}#ic_vertical_align_bottom_24px`} />
            </svg>
            {t(r => r.downloadAlbumLink)}…
          </Button>
        ) : null}
        {album.credits.photographer ? (
          <LinkContainer to={album.credits.photographer.path}>
            <Button variant="link" size="sm">
              <svg className="BreadcrumbBar-icon">
                <use xlinkHref={`${socialIcons}#ic_person_24px`} />
              </svg>
              {t(r => r.aboutPhotographerLink)}
            </Button>
          </LinkContainer>
        ) : null}
      </nav>

      <DownloadDialog
        key={album.path}
        album={album}
        onAccept={downloadAlbum}
        onClose={closeDownloadDialog}
        isOpen={isDownloadDialogOpen}
        isPreparing={isDownloadPreparing}
        t={T(r => r.DownloadAlbumDialog)}
      />
    </Container>
  );
}

export default BreadcrumbBar;
