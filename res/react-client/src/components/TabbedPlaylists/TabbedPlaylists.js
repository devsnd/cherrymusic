import React, {PropTypes} from 'react';
import { bindActionCreators } from 'redux'
import { connect } from 'react-redux';
import {PLAYBACK_ENDED} from 'redux/modules/Player';
import CMComponent from 'utils/CMComponent';

import {Tab, Tabs, Table} from 'react-bootstrap';

import TrackListItem from 'components/TrackListItem/TrackListItem';
import ScrollableView from 'components/ScrollableView/ScrollableView';

import {
  createPlaylist,
  activatePlaylist,
  setPlayingPlaylist,
  playTrackInPlaylist,
  closePlaylist,
  selectActivePlaylistId,
} from 'redux/modules/PlaylistManager';

import {
  playlistStates,
  selectEntitiesPlaylist,
} from 'redux/modules/CherryMusicApi';

class TabbedPlaylists extends CMComponent {
  static propTypes = {
    // attrs
    height: PropTypes.number.isRequired,
    // redux
    openPlaylistIds: PropTypes.array.isRequired,
  };

  constructor (props) {
    super(props);
    this.state = {};
    this._newPlaylistPlaceholder = {};
    this.renderPlaylistItems = this.renderPlaylistItems.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
  }

  selectTrack (playlist, tracknr) {
    this.setPlayingPlaylist(playlist);
    this.playTrackInPlaylist(playlist, tracknr);
  }

  handleSelect (playlist) {
    console.log(playlist);
    if (playlist === this._newPlaylistPlaceholder){
      this.createPlaylist(true);
    } else {
      this.props.activatePlaylist(playlist);
    }
  }

  renderPlaylistItems (playlist) {
    return playlist.trackIds.map((trackId, idx) => {
      const track = this.props.entities.track[trackId];
      return (
        <div
          key={idx}
          onClick={() => {this.selectTrack(playlist, idx)}}
          style={makeTrackStyle(playlist, idx, track)}
        >
          <TrackListItem
            track={track}
          />
        </div>
      );
    })
  }

  safeRender () {
    const isPlayingTrack = (playlist, idx) => {
      return (
        playlist === this.props.playingPlaylist &&
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

    const makePlaylistTabStyle = (playlist) => {
      const style = {};
      if (playlist.state === playlistStates.new) {
        style.fontStyle = 'italic';
        style.fontWeight = 900;
      }
      return style;
    };

    return (
      <Tabs activeKey={this.props.activePlaylistId} onSelect={this.handleSelect}>
        {this.props.openPlaylistIds.map((playlistId) => {
          const playlist = this.props.playlistEntities[playlistId];
          return (
            <Tab
              key={playlist.randid}
              eventKey={playlist.id}
              title={
                <span style={makePlaylistTabStyle(playlist)}>
                  {playlist.name}
                  <span
                    onClick={() => { this.closePlaylist(playlist) }}
                    style={{'fontWeight': 900}}
                  >
                    ×
                  </span>
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
                  {playlist.state === playlistStates.loading &&
                    <span>
                      loading...
                    </span>
                  }
                  {playlist.state !== playlistStates.loading &&
                    this.renderPlaylistItems(playlist)
                  }
                </div>
              </ScrollableView>
            </Tab>
          );
        })}
        <Tab eventKey={this._newPlaylistPlaceholder} title="+" />
      </Tabs>
    )
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
    createPlaylist: createPlaylist,
    activatePlaylist: activatePlaylist,
    setPlayingPlaylist: setPlayingPlaylist,
    playTrackInPlaylist: playTrackInPlaylist,
    closePlaylist: closePlaylist,
  }
)(TabbedPlaylists);

