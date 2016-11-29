import React, {PropTypes} from 'react';
import loadingImage from 'static/img/cherrymusic_loader.gif';

export class Loader extends React.Component {
  render () {
    return <img src={loadingImage} />
  }
}

export default Loader;
