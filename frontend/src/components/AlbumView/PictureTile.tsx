import * as React from "react";
import { Link } from 'react-router-dom';


interface PictureTileProps {
  path: string;
  height: number;
  width: number;
  title?: string;
  src?: string;
}


export default class PictureTile extends React.PureComponent<PictureTileProps> {
  render() {
    const { path, width, height, src, title } = this.props;

    return (
      <Link
        className="AlbumView-tile"
        to={path}
      >
        {src ? (
          <img
            src={src}
            style={{
              display: "block",
              width,
              height,
            }}
          />
        ) : null}
        {title ? <div className="PictureTile-title">{title}</div> : null}
      </Link>
    );
  }
}
