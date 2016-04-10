import React, {PropTypes} from 'react';
import { bindActionCreators } from 'redux'
import { connect } from 'react-redux';
import {PLAYBACK_ENDED} from 'redux/modules/Player';

import {Tab, Tabs, Table} from 'react-bootstrap';

import {
  createPlaylist,
  activatePlaylist,
  setPlayingPlaylist,
  playTrackInPlaylist,
  closePlaylist,
  playlistStates,
} from 'redux/modules/Playlist';

class TabbedPlaylists extends React.Component {
  static propTypes = {
    playlists: PropTypes.array.isRequired,
  };

  constructor (props) {
    super(props);
    this.state = {};
    this._newPlaylistPlaceholder = {};
    this.createPlaylist = bindActionCreators(this.props.createPlaylist, this.props.dispatch);
    this.activatePlaylist = bindActionCreators(this.props.activatePlaylist, this.props.dispatch);
    this.setPlayingPlaylist = bindActionCreators(this.props.setPlayingPlaylist, this.props.dispatch);
    this.playTrackInPlaylist = bindActionCreators(this.props.playTrackInPlaylist, this.props.dispatch);
    this.closePlaylist = bindActionCreators(this.props.closePlaylist, this.props.dispatch);
  }

  selectTrack (playlist, tracknr) {
    this.setPlayingPlaylist(playlist);
    this.playTrackInPlaylist(playlist, tracknr);
  }

  handleSelect (playlist) {
    if (playlist === this._newPlaylistPlaceholder){
      this.createPlaylist(true);
    } else {
      this.activatePlaylist(playlist);
    }
  }

  render () {
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
      <Tabs activeKey={this.props.activePlaylist} onSelect={this.handleSelect.bind(this)}>
        {this.props.playlists.map((playlist) => {
          return (
            <Tab
              key={playlist.randid}
              eventKey={playlist}
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
              <div style={{
                overflow: 'auto',
                height: '200px',
                borderLeft: '1px solid #ddd',
              }}>
                  {playlist.tracks.map((track, idx) => {
                    return (
                      <div
                        key={idx}
                        onClick={() => {this.selectTrack(playlist, idx)}}
                        style={makeTrackStyle(playlist, idx, track)}
                      >
                        <span>{track.label}</span>
                        <span>{track.path}</span>
                      </div>
                    );
                  })}
              </div>
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
      playlists: state.playlist.playlists,
      activePlaylist: state.playlist.activePlaylist,
      playingPlaylist: state.playlist.playingPlaylist,
      playingTrackIdx: state.playlist.playingTrackIdx,
    };
  },
  (dispatch) => {
    return {
      dispatch: dispatch,
      createPlaylist: createPlaylist,
      activatePlaylist: activatePlaylist,
      setPlayingPlaylist: setPlayingPlaylist,
      playTrackInPlaylist: playTrackInPlaylist,
      closePlaylist: closePlaylist,
    };
  }
)(TabbedPlaylists);

