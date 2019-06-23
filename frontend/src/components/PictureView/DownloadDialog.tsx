import React from 'react';
import Album from '../../models/Album';
import Picture from '../../models/Picture';
import { Translation } from 'react-i18next';
import Linebreaks from '../Linebreaks';


interface DownloadDialogProps {
  picture: Picture;
  album: Album;
  onClose(): void;
}


const DownloadDialog: React.FC<DownloadDialogProps> = ({ album, picture, onClose }) => {
  const [isTermsAndConditionsAccepted, setTermsAndConditionsAccepted] = React.useState(false);
  const toggleTermsAndConditionsAccepted = () => setTermsAndConditionsAccepted(!isTermsAndConditionsAccepted);

  const text = album && album.terms_and_conditions ? album.terms_and_conditions.text : '';
  const { photographer, director } = album.credits;

  const haveTwitter = (photographer && photographer.twitter_handle) || (director && director.twitter_handle);
  const haveInstagram = (photographer && photographer.instagram_handle) || (director && director.instagram_handle);
  const haveCredit = (photographer && photographer.display_name) || (director && director.display_name);

  return (
    <Translation ns="DownloadDialog">
      {(t) => (
        <div className="DownloadDialog modal fade show" style={{ display: "block" }} role="dialog">
          <div className="modal-dialog" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">{t('dialogTitle')}</h5>
                <button type="button" className="close" onClick={onClose} aria-label="Close">
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>

              <div className="modal-body">
                <p><strong>{t('termsAndConditions')}</strong></p>
                <Linebreaks text={text || t('defaultTerms')} />

                {photographer && photographer.email ? <p><strong>{t('contact')}</strong> {photographer.email}</p> : null}

                {haveTwitter ? (
                  <>
                    <p><strong>{t('twitterCredit')}</strong></p>
                    <p>
                      {photographer ? <>📸{photographer.twitter_handle ? `@${photographer.twitter_handle}` : photographer.display_name} </> : null}
                      {director ? <>📸{director.twitter_handle ? `@${director.twitter_handle}` : director.display_name} </> : null}
                    </p>
                  </>
                ) : null}

                {haveInstagram ? (
                  <>
                    <p><strong>{t('instagramCredit')}</strong></p>
                    <p>
                      {photographer ? <>{t('photographer')}: {photographer.instagram_handle ? `@${photographer.instagram_handle}` : photographer.display_name}<br /></> : null}
                      {director ? <>{t('director')}: {director.instagram_handle ? `@${director.instagram_handle}` : director.display_name}<br/></> : null}
                    </p>
                  </>
                ) : null}

                {haveCredit ? (
                  <>
                    <p><strong>{haveTwitter || haveInstagram ? t('genericCredit') : t('genericCreditAlternative')}</strong></p>
                    <p>
                      {photographer && photographer.display_name ? <>{t('photographer')}: {photographer.display_name}<br /></> : null}
                      {director && director.display_name ? <>{t('director')}: {director.display_name}<br /></> : null}
                    </p>
                  </>
                ) : null}

                <label className="mt-3">
                  <input type="checkbox" checked={isTermsAndConditionsAccepted} onChange={toggleTermsAndConditionsAccepted} />
                  {' ' + t('acceptTermsAndConditions')}
                </label>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={!isTermsAndConditionsAccepted}
                  onClick={() => { window.open(picture.original.src); }}
                >
                  {t('downloadButtonText')}
                </button>
                <button type="button" className="btn btn-secondary" onClick={onClose}>{t('closeButtonText')}</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Translation>
  );
}

export default DownloadDialog;