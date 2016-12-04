import {connect} from 'react-redux';
import {Center} from 'components/helper/Center';
import {Loader} from 'components/Loader/Loader';
import {selectEntitiesPlaylist} from 'redux/modules/CherryMusicApi';
import {Button, Modal} from 'react-bootstrap';
import React, {PropTypes } from 'react';

import {actionPlaylistDeleteRequested } from 'redux/modules/CherryMusicApi';


export class DeletePlaylistModal extends React.Component {
  static propTypes = {
    playlist: PropTypes.object,
    show: PropTypes.bool.isRequired,
    onCancel: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    // redux
    playlistEntities: PropTypes.object.isRequired,
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
            Really delete Playlist "{playlist.title}"?
          </Modal.Header>
          <Modal.Body>
            Do you really want to delete this precious playlist?
          </Modal.Body>
          <Modal.Footer>
            <Button
              bsStyle="danger"
              onClick={this.props.onDelete}
            >
              Yes, get it out of my life
            </Button>
            <Button
              bsStyle="default"
              onClick={this.props.onCancel}
            >
              No, leave it as it is
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  }
}

export default DeletePlaylistModal;

