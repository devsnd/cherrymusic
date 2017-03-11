import {Center} from 'components/helper/Center';
import Loader from 'components/Loader/Loader';
import {connect} from 'react-redux';
import {selectEntitiesPlaylist} from 'redux/modules/CherryMusicApi';
import {
  Button,
  Modal,
  FormControl,
  FormGroup,
  ControlLabel,
  Checkbox,
} from 'react-bootstrap';
import React, {PropTypes } from 'react';

export class SavePlaylistModal extends React.Component {
  static propTypes = {
    playlist: PropTypes.object,
    show: PropTypes.bool.isRequired,
    onCancel: PropTypes.func.isRequired,
    onSave: PropTypes.func.isRequired,
    isSaving: PropTypes.bool.isRequired,
  };

  constructor (props) {
    super(props);
    this.state = {
      // is filled when receiving props
      playlistTitle: '',
      playlistPublic: true,
    };
    this.handleSave = this.handleSave.bind(this);
    this.handleKeyDown = this.handleKeyDown.bind(this);
    this.handleChangeTitle = this.handleChangeTitle.bind(this);
    this.handleTogglePublic = this.handleTogglePublic.bind(this);
    this.handleCancelModal = this.handleCancelModal.bind(this);
  }

  componentWillReceiveProps (props) {
    if (this.props.playlist !== props.playlist) {
      // if a new playlist was inserted, update the title and public flags
      this.setState({
        playlistTitle: props.playlist.title,
        playlistPublic: (
          typeof props.playlist.public !== 'undefined'
            ? props.playlist.public
            : true  // make new playlists public by default
        ),
      });
    }
  }

  handleChangeTitle (evt) {
    this.setState({playlistTitle: evt.target.value});
  }

  handleTogglePublic (evt) {
    this.setState({playlistPublic: !this.state.playlistPublic});
  }

  handleCancelModal () {
    if (!this.props.isSaving) {
      this.props.onCancel();
    }
  }

  handleKeyDown (evt) {
    // trigger save when pressing enter
    const KEY_ENTER = 13;
    if (evt.keyCode === KEY_ENTER) {
      this.handleSave();
    }
  }

  handleSave () {
    this.props.onSave({
      title: this.state.playlistTitle,
      isPublic: this.state.playlistPublic,
    });
  }

  render () {
    const playlist = this.props.playlist;
    if (typeof playlist === 'undefined') {
      return (
        <div></div>
      );
    }
    return (
      <div>
        <Modal
          show={this.props.show}
          onHide={this.handleCancelModal}
          onEntered={this.focusTitleInput}
        >
          <Modal.Header>
            Save playlist
          </Modal.Header>
          {this.props.isSaving ? (
            <Modal.Body>
              <Center>
                <Loader />
              </Center>
            </Modal.Body>
          ) : (
            <Modal.Body>
              <FormGroup>
                <ControlLabel>Playlist Title:</ControlLabel>
                <FormControl
                  autoFocus
                  type="text"
                  value={this.state.playlistTitle}
                  placeholder="Enter playlist Title"
                  onChange={this.handleChangeTitle}
                  onKeyDown={this.handleKeyDown}
                />
              </FormGroup>
              <FormGroup>
                <Checkbox
                  inline
                  style={{position: 'relative', top: '-10px'}} /* to line up with the Label */
                  checked={this.state.playlistPublic}
                  onClick={this.handleTogglePublic}
                />
                <ControlLabel inline>
                  Playlist visible to other users
                </ControlLabel>
              </FormGroup>
            </Modal.Body>
          )}
          <Modal.Footer>
            <Button
              disabled={this.props.isSaving}
              bsStyle="primary"
              onClick={this.handleSave}
            >
              Save Playlist
            </Button>
            <Button
              disabled={this.props.isSaving}
              bsStyle="default"
              onClick={this.handleCancelModal}
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

