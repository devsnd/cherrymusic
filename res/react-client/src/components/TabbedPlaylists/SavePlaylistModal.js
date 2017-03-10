import {connect} from 'react-redux';
import {selectEntitiesPlaylist} from 'redux/modules/CherryMusicApi';
import {Button, Modal} from 'react-bootstrap';
import React, {PropTypes } from 'react';

export class SavePlaylistModal extends React.Component {
  static propTypes = {
    playlist: PropTypes.object,
    show: PropTypes.bool.isRequired,
    onCancel: PropTypes.func.isRequired,
    onSave: PropTypes.func.isRequired,
  };

  render () {
    const playlist = this.props.playlist;
    if (typeof playlist === 'undefined') {
      return (
        <div></div>
      );
    }
    return (
      <div>
        <Modal show={this.props.show} onHide={this.props.onCancel}>
          <Modal.Header>
            Save playlist
          </Modal.Header>
          <Modal.Body>
            name: <input type="text" />
          </Modal.Body>
          <Modal.Footer>
            <Button
              bsStyle="primary"
              onClick={this.props.onSave}
            >
              Save Playlist
            </Button>
            <Button
              bsStyle="default"
              onClick={this.props.onCancel}
            >
              Cancel
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }
}

export default SavePlaylistModal;

