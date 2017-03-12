import React, {PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import PureRenderMixin from 'react-addons-pure-render-mixin';

import {errorMessage} from 'redux/modules/Messages';
import {PLAYBACK_ENDED } from 'redux/modules/Player';
import SavePlaylistModal from './SavePlaylistModal';

import {
  MenuItem,
  DropdownButton,
  ButtonGroup,
  Button,
  Tab,
  Tabs,
  Table,
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
  replacePlaylist,
} from 'redux/modules/PlaylistManager';

import {
  playlistStates,
  selectEntitiesPlaylist,
  sortPlaylistTracksBy,
  saveNewPlaylist,
  fetchPlaylistDetailThunk,
} from 'redux/modules/CherryMusicApi';

class TabbedPlaylists extends React.Component {
  static propTypes = {
    // attrs
    height: PropTypes.number.isRequired,
    style: PropTypes.object,
    // redux
    openPlaylistIds: PropTypes.array.isRequired,
  };

  constructor (props) {
    super(props);
    this.shouldComponentUpdate = PureRenderMixin.shouldComponentUpdate.bind(this);

    this.state = {
      playlistToSave: null,
      showSavePlaylistModal: false,
      isSavingPlaylist: false,
    };
    this.handleCancelSavePlaylistModal = () => { this.setState({showSavePlaylistModal: false}); };
    this.handleOpenSavePlaylistModal = this.handleOpenSavePlaylistModal.bind(this);
    this.handleSavePlaylistModal = this.handleSavePlaylistModal.bind(this);

    this._newPlaylistPlaceholder = {};
    this.renderActivePlaylistTracks = this.renderActivePlaylistTracks.bind(this);
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
    };
  }

  handleSavePlaylistModal (playlistData) {
    this.setState({isSavingPlaylist: true});
    // if the playlist id is < 0 it means that the id is local and not saved
    // to the server yet, so we call `saveNewPlaylist`
    if (this.state.playlistToSave.plid < 0) {
      const localPlaylistId = this.state.playlistToSave.plid;
      this.props.saveNewPlaylist(
        localPlaylistId,
        playlistData.title,
        playlistData.isPublic,
      ).then(
        (playlistData) => {
          const newPlaylistId = playlistData.id;
          this.setState({
            isSavingPlaylist: false,
            showSavePlaylistModal: false,
          });
          this.props.replacePlaylist(localPlaylistId, newPlaylistId)
        },
        (error) => {
          // saving either failed because the server is down, or because the
          // playlist name already exists. unfortunately the legacy API just
          // delivers ugly HTML
          this.props.errorMessage(`A playlist with that name already exists. Please use
          another name or try again later`);
          console.error(error);
          this.setState({isSavingPlaylist: false});
        },
      );
    } else {
      alert('updating of existing playlist is not implemented');
    }
  }

  handleOpenSavePlaylistModal () {
    this.setState({
      playlistToSave: this.props.activePlaylist,
      showSavePlaylistModal: true,
    });
  }

  renderPlaylistActions (playlist) {
    const playlistId = playlist.plid;
    return (
      <div style={{padding: '10px 0'}} key={'pl-actions'}>
        <Button
          bsStyle="primary"
          bsSize="xsmall"
          onClick={this.handleOpenSavePlaylistModal}
          disabled={playlist.trackIds.length === 0}
        >
          save
        </Button>
        <ButtonGroup>
          <DropdownButton
            key={0}
            id="playlist-sort-options"
            bsSize="xsmall"
            title="sort"
            onSelect={this.handleSort(playlistId)}
          >
            <MenuItem key={0} eventKey="track">by track number</MenuItem>
            <MenuItem key={1} eventKey="title">by title</MenuItem>
            <MenuItem key={2} eventKey="artist">by artist</MenuItem>
          </DropdownButton>
          <Button
            key={1}
            onClick={() => alert('not implemented')}
            bsSize="xsmall">
            download
          </Button>
        </ButtonGroup>
      </div>
    );
  }

  renderActivePlaylistTracks (playlist, tracks) {
    const isPlayingTrack = (playlist, idx) => {
      return (
        playlist.plid === this.props.activePlaylist.plid &&
        idx === this.props.playingTrackIdx
      );
    };

    const playingStyle = {backgroundColor: '#ddeedd'};
    const nonPlayingStyle = {};

    return tracks.map((track, idx) => {
      const isPlaying = isPlayingTrack(playlist, idx);
      return (
        <div
          key={idx}
          onClick={() => this.selectTrack(playlist, idx)}
          style={isPlaying ? playingStyle : nonPlayingStyle}
        >
          <TrackListItem track={track} compact />
        </div>
      );
    });
  }

  render () {
    const makePlaylistTabStyle = (playlist) => {
      const style = {};
      if (playlist.state === playlistStates.new) {
        style.fontStyle = 'italic';
        style.fontWeight = 900;
      }
      return style;
    };

    const style = this.props.style || {};
    const activePlaylist = this.props.activePlaylist;
    const activePlaylistTracks = this.props.activePlaylistTracks;
    const activeTabKey = (
      typeof this.props.activePlaylist === 'undefined'
        ? '-'
        : this.props.activePlaylist.plid
    );

    return (
      <div>
        <SavePlaylistModal
          playlist={this.state.playlistToSave}
          show={this.state.showSavePlaylistModal}
          onCancel={this.handleCancelSavePlaylistModal}
          onSave={this.handleSavePlaylistModal}
          isSaving={this.state.isSavingPlaylist}
        />
        <Tabs
          activeKey={activeTabKey}
          onSelect={this.handleTabSelect}
          style={style}
          id="playlist-tabs-container"
        >
          {this.props.openPlaylists.map((playlist) => {
            return (
              <Tab
                key={playlist.plid}
                eventKey={playlist.plid}
                title={
                  <span style={makePlaylistTabStyle(playlist)}>
                    {playlist.title}
                    <Button
                      bsSize="xsmall"
                      onClick={() => { this.props.closePlaylistTab(playlist.plid); }}
                      style={{fontWeight: 900, fontStyle: 'normal', marginLeft: 10}}
                    >
                      ×
                    </Button>
                  </span>
                }
              >
              </Tab>
            );
          })}
          <Tab key={'+'} eventKey={this._newPlaylistPlaceholder} title="+" />
        </Tabs>
        {/* for some reason the pure render mixin does not play nice with the
        react-bootstrap tabs, so we render the active playlist below the tabs,
        instead of inside them
         */}
        {typeof activePlaylist === 'undefined' ? (
          <span>initializing...</span>
        ) : (
          <ScrollableView height={
            this.props.height - 44 /* tab height */
          }>
            <div style={{
              /* let the line of the tab continue as a separator to the
               file browser: */
              borderLeft: '1px solid #ddd',
              minHeight: '100%',
            }}>
              {typeof activePlaylist.trackIds === 'undefined' ? (
                  <span>
                loading...
              </span>
                ) : (
                  <div style={{paddingLeft: 10}}>
                    {this.renderPlaylistActions(activePlaylist)}
                    {this.renderActivePlaylistTracks(activePlaylist, activePlaylistTracks)}
                  </div>
                )}
            </div>
          </ScrollableView>
        )}
      </div>
    );
  }
}

export default connect(
  (state, dispatch) => {
    const playlistEntities = selectEntitiesPlaylist(state);
    const activePlaylist = playlistEntities[selectActivePlaylistId(state)];
    return {
      openPlaylists: state.playlist.openPlaylistIds.map(
        (openPlaylistId) => playlistEntities[openPlaylistId]
      ),
      activePlaylist: activePlaylist,
      activePlaylistTracks: (
        typeof activePlaylist === 'undefined' ? (
          []
        ) : (
          activePlaylist.trackIds.map((trackId) => state.api.entities.track[trackId])
        )
      ),
      playingPlaylist: state.playlist.playingPlaylist,
      playingTrackIdx: state.playlist.playingTrackIdx,
    };
  },
  {
    sortPlaylistTracksBy: sortPlaylistTracksBy,
    createPlaylist: createPlaylist,
    activatePlaylist: activatePlaylist,
    setPlayingPlaylist: setPlayingPlaylist,
    playTrackInPlaylist: playTrackInPlaylist,
    closePlaylistTab: closePlaylistTab,
    saveNewPlaylist: saveNewPlaylist,
    errorMessage: errorMessage,
    replacePlaylist: replacePlaylist,
    fetchPlaylistDetailThunk: fetchPlaylistDetailThunk,
  }
)(TabbedPlaylists);

