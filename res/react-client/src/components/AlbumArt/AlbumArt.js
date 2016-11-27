import React, {PropTypes} from 'react';
import folderImage from 'static/img/folder.png';
import {fetchAlbumArt} from 'redux/modules/CherryMusicApi';
import {connect} from 'react-redux';
import classes from 'utils/animations/Pulse.scss';

const loading = 0;
const loaded = 1;
const error = 2;

export class AlbumArt extends React.Component {
  static propTypes = {
    directory: PropTypes.string.isRequired,
    style: PropTypes.object,
  };

  constructor (props) {
    super(props);
    this.state = {
      loadingState: loading,
      b64image: null,
    }
  }

  componentDidMount () {
    this.props.fetchAlbumArt(this.props.directory).then(
      (data) => {
      this.setState({
          b64image: 'data:image/jpg;base64,' + data.image,
          loadingState: loaded,
        });
      },
      () => this.setState({
        loadingState: error
      })
    );
  }

  render () {
    const style = this.props.style || style;
    let imageUrl;
    let cssClass;
    if (this.state.loadingState === loading) {
      imageUrl = folderImage;
      cssClass = {className: classes.pulse}
    } else if (this.state.loadingState === error) {
      imageUrl = folderImage;
      cssClass = {}
    } else {
      imageUrl = this.state.b64image;
      cssClass = {}
    }

    return (
      <div
        {...cssClass}
        style={{
          backgroundImage: 'url(' + imageUrl + ')',
          backgroundSize: 'cover',
          width: 50,
          height: 50,
          ...style,
        }}
      ></div>
    );
  }
}

export default connect(
  null,
  {
    fetchAlbumArt: fetchAlbumArt,
  }
)(AlbumArt);
