import React, {PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import {PLAYBACK_ENDED } from 'redux/modules/Player';
import CMComponent from 'utils/CMComponent';
import SavePlaylistModal from './SavePlaylistModal';

import {
  MenuItem,
  DropdownButton,
  ButtonGroup,
  Button,
  Tab,
  Tabs,
  Table
} from 'react-bootstrap';

import TrackListItem from 'components/TrackListItem/TrackListItem';
import ScrollableView from 'components/ScrollableView/ScrollableView';

import {
  createPlaylist,
  activatePlaylist,
  setPlayingPlaylist,
  playTrackInPlaylist,
  closePlaylistTab,
  selectActivePlaylistId,
} from 'redux/modules/PlaylistManager';

import {
  playlistStates,
  selectEntitiesPlaylist,
  sortPlaylistTracksBy,
} from 'redux/modules/CherryMusicApi';

class TabbedPlaylists extends CMComponent {
  static propTypes = {
    // attrs
    height: PropTypes.number.isRequired,
    style: PropTypes.object,
    // redux
    openPlaylistIds: PropTypes.array.isRequired,
  };

  constructor (props) {
    super(props);
    this.state = {
      playlistToSave: null,
      showSavePlaylistModal: false,
    };
    this.handleCancelSavePlaylistModal = this.handleCancelSavePlaylistModal.bind(this);
    this.handleOpenSavePlaylistModal = this.handleOpenSavePlaylistModal.bind(this);
    this.handleSavePlaylistModal = this.handleSavePlaylistModal.bind(this);

    this._newPlaylistPlaceholder = {};
    this.renderPlaylistItems = this.renderPlaylistItems.bind(this);
    this.handleSort = this.handleSort.bind(this);
    this.renderPlaylistActions = this.renderPlaylistActions.bind(this);
    this.handleTabSelect = this.handleTabSelect.bind(this);
  }

  selectTrack (playlist, tracknr) {
    this.props.setPlayingPlaylist(playlist);
    this.props.playTrackInPlaylist(playlist, tracknr);
  }

  handleTabSelect (playlist) {
    if (playlist === this._newPlaylistPlaceholder) {
      this.props.createPlaylist();
    } else {
      this.props.activatePlaylist(playlist);
    }
  }

  handleSort (playlistId) {
    return (eventKey) => {
      this.props.sortPlaylistTracksBy(playlistId, eventKey);
    }
  }

  handleCancelSavePlaylistModal () {
    this.setState({
      playlistToSave: null,
      showSavePlaylistModal: false
    });
  }

  handleSavePlaylistModal () {
    alert('not implemented!')
  }

  handleOpenSavePlaylistModal () {
    const activatePlaylist = this.props.playlistEntities[this.props.activePlaylistId];
    this.setState({
      playlistToSave: activatePlaylist,
      showSavePlaylistModal: true,
    })
  }

  renderPlaylistActions (playlist) {
    const playlistId = playlist.plid;
    return (
      <div style={{padding: 10}}>
        <Button bsStyle="primary" bsSize="xsmall" onClick={this.handleOpenSavePlaylistModal}>
          save
        </Button>
        <ButtonGroup>
          <DropdownButton
            id="playlist-sort-options"
            bsSize="xsmall"
            title="sort"
            onSelect={this.handleSort(playlistId)}
          >
            <MenuItem eventKey="track">by track number</MenuItem>
            <MenuItem eventKey="title">by title</MenuItem>
            <MenuItem eventKey="artist">by artist</MenuItem>
          </DropdownButton>
          <Button
            onClick={() => alert('not implemented')}
            bsSize="xsmall">
            download
          </Button>
        </ButtonGroup>
      </div>
    );
  }

  renderPlaylistItems (playlist) {
    const isPlayingTrack = (playlist, idx) => {
      return (
        playlist.plid === this.props.activePlaylistId &&
        idx === this.props.playingTrackIdx
      );
    };

    const makeTrackStyle = (playlist, idx, track) => {
      const style = {};
      if (isPlayingTrack(playlist, idx)) {
        style.backgroundColor = '#ddeedd';
      }
      return style;
    };

    return playlist.trackIds.map((trackId, idx) => {
      const track = this.props.entities.track[trackId];
      return (
        <div
          key={idx}
          onClick={() => { this.selectTrack(playlist, idx); }}
          style={makeTrackStyle(playlist, idx, track)}
        >
          <TrackListItem
            track={track}
          />
        </div>
      );
    });
  }

  safeRender () {
    const makePlaylistTabStyle = (playlist) => {
      const style = {};
      if (playlist.state === playlistStates.new) {
        style.fontStyle = 'italic';
        style.fontWeight = 900;
      }
      return style;
    };

    const style = this.props.style || {};

    return (
      <div>
        <SavePlaylistModal
          playlist={this.state.playlistToSave}
          show={this.state.showSavePlaylistModal}
          onCancel={this.handleCancelSavePlaylistModal}
          onSave={this.handleSavePlaylistModal}
        />
        <Tabs
          activeKey={this.props.activePlaylistId}
          onSelect={this.handleTabSelect}
          style={style}
          id="playlist-tabs-container"
        >
          {this.props.openPlaylistIds.map((playlistId) => {
            const playlist = this.props.playlistEntities[playlistId];
            return (
              <Tab
                key={playlist.plid}
                eventKey={playlist.plid}
                title={
                  <span style={makePlaylistTabStyle(playlist)}>
                    {playlist.title}
                    <Button
                      bsSize="xsmall"
                      onClick={() => { this.props.closePlaylistTab(playlistId); }}
                      style={{fontWeight: 900, fontStyle: 'normal', marginLeft: 10}}
                    >
                      ×
                    </Button>
                  </span>
                }
              >
                <ScrollableView height={
                  this.props.height - 44 /* tab height */
                }>
                  <div style={{
                    /* let the line of the tab continue as a separator to the
                    file browser: */
                    borderLeft: '1px solid #ddd',
                    minHeight: '100%',
                  }}>
                    {typeof playlist.trackIds === 'undefined' ? (
                      <span>
                        loading...
                      </span>
                    ) : (
                      <div>
                        {this.renderPlaylistActions(playlist)}
                        {this.renderPlaylistItems(playlist)}
                      </div>
                    )}
                  </div>
                </ScrollableView>
              </Tab>
            );
          })}
          <Tab eventKey={this._newPlaylistPlaceholder} title="+" />
        </Tabs>
      </div>
    );
  }
}

export default connect(
  (state, dispatch) => {
    return {
      openPlaylistIds: state.playlist.openPlaylistIds,
      activePlaylistId: selectActivePlaylistId(state),
      playlistEntities: selectEntitiesPlaylist(state),
      playingPlaylist: state.playlist.playingPlaylist,
      playingTrackIdx: state.playlist.playingTrackIdx,
      entities: state.api.entities,
    };
  },
  {
    sortPlaylistTracksBy: sortPlaylistTracksBy,
    createPlaylist: createPlaylist,
    activatePlaylist: activatePlaylist,
    setPlayingPlaylist: setPlayingPlaylist,
    playTrackInPlaylist: playTrackInPlaylist,
    closePlaylistTab: closePlaylistTab,
  }
)(TabbedPlaylists);

