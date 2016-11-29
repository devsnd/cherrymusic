import {connect} from 'react-redux';
import {Center} from 'components/helper/Center';
import {Loader} from 'components/Loader/Loader';
import {selectEntitiesPlaylist} from 'redux/modules/CherryMusicApi';
import {Button, Modal} from 'react-bootstrap';
import React, {PropTypes } from 'react';

import {actionPlaylistDeleteRequested } from 'redux/modules/CherryMusicApi';


class DeletePlaylistModal extends React.Component {
  static propTypes = {
    playlistId: PropTypes.number,
    show: PropTypes.bool.isRequired,
    onCancel: PropTypes.func.isRequired,
    // redux
    playlistEntities: PropTypes.object.isRequired,
    deletePlaylist: PropTypes.func.isRequired,
  };

  constructor (props) {
    super(props);
    this.state = {busy: false};
    this.handleDeletePlaylist = ::this.handleDeletePlaylist;
  }

  handleDeletePlaylist () {
    this.setState({busy: true});
    this.props.deletePlaylist(this.props.playlistId).then(() => {
      this.setState({busy: false});
    });
  }

  render () {
    const playlist = this.props.playlistEntities[this.props.playlistId];
    return (
      <div>
        <Modal show={this.props.show} onHide={this.props.onCancel}>
          {this.props.playlistId === null || this.state.busy ? (
            <Center><Loader /></Center>
          ) : (
            [
              <Modal.Header>
                Really delete Playlist "{playlist.title}"?
              </Modal.Header>
              ,
              <Modal.Body>
                Do you really want to delete this precious playlist?
              </Modal.Body>
              ,
              <Modal.Footer>
                <Button
                  bsStyle="danger"
                  onClick={this.handleDeletePlaylist}
                >
                  Yes, get it out of my life
                </Button>
                <Button
                  bsStyle="default"
                  onClick={this.props.onCancel}
                >
                  No, leave it as it is
                </Button>
              </Modal.Footer>,
            ]
          )}
        </Modal>
      </div>
    );
  }
}

export default connect(
  (state) => ({
    playlistEntities: selectEntitiesPlaylist(state),
  }),
  {
    deletePlaylist: actionPlaylistDeleteRequested,
  }
)(DeletePlaylistModal);
