import {
  actionPlaylistDeleteRequested,
  actionPlaylistSetPublicRequested
} from 'redux/modules/CherryMusicApi';
import {selectEntitiesPlaylist} from 'redux/modules/CherryMusicApi';
import React, {PropTypes } from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import {
  ListGroup,
  ListGroupItem,
  Label,
  Badge,
  ButtonGroup,
  Button,
} from 'react-bootstrap';
import Username from 'components/Username/Username';
import ScrollableView from 'components/ScrollableView/ScrollableView';
import DeletePlaylistModal from './DeletePlaylistModal';
import PlaylistBrowserItem from './PlaylistBrowserItem';

import {
  // playlist listing
  selectSortedPlaylists,
  selectPlaylistsLoadingState,
  selectPlaylistIds,
  selectPlaylistSortBy,
  selectPlaylistSortByReversed,
  PlaylistSortModes as SortModes,
  actionPlaylistListSortBy,
  LoadingStates,
  // opening playlists
  actionPlaylistOpenRequested,
} from 'redux/modules/CherryMusicApi';
import Age from 'components/Age/Age';

class PlaylistBrowser extends React.Component {
  static propTypes = {
    // attrs
    height: PropTypes.number,
  };

  constructor (props) {
    super(props);
    this.sortByTitle = () => {
      this.props.sortByTitle();
    };
    this.sortByAge = () => {
      this.props.sortByAge();
    };
    this.sortByUsername = () => {
      this.props.sortByUsername();
    };
    this.handleDeletePlaylist = ::this.handleDeletePlaylist;
    this.handleOpenPlaylist = ::this.handleOpenPlaylist;
    this.handleCancelDeletePlaylistModal = ::this.handleCancelDeletePlaylistModal;
    this.handleConfirmDeletePlaylistModal = ::this.handleConfirmDeletePlaylistModal;
    this.state = {
      showDeletePlaylistModal: false,
      deletePlaylistId: null,
    };
  }

  handleOpenPlaylist (playlistId) {
    return () => this.props.openPlaylist(playlistId);
  }

  handleDeletePlaylist (playlistId) {
    return (evt) => {
      evt.stopPropagation();
      this.setState({
        showDeletePlaylistModal: true,
        deletePlaylistId: playlistId,
      });
    };
  }

  handleCancelDeletePlaylistModal () {
    this.setState({
      showDeletePlaylistModal: false,
      deletePlaylistId: null,
    });
  }

  handleConfirmDeletePlaylistModal () {
    this.props.requestPlaylistDelete(this.state.deletePlaylistId);
    this.setState({
      showDeletePlaylistModal: false,
      deletePlaylistId: null,
    });
  }

  handleSetPlaylistPublic (playlistId) {
    return (evt) => {
      evt.stopPropagation();
      this.props.requestPlaylistSetPublic(playlistId);
    }
  }

  render () {
    const {sortedPlaylists, loadingState, sortBy, playlistEntities} = this.props;
    const deletablePlaylist = playlistEntities[this.state.deletePlaylistId];
    return (
      <div>
        <DeletePlaylistModal
          playlist={deletablePlaylist}
          show={this.state.showDeletePlaylistModal}
          onCancel={this.handleCancelDeletePlaylistModal}
          onDelete={this.handleConfirmDeletePlaylistModal}
        />
        {loadingState === LoadingStates.loading && <div>
          loading...
        </div>}
        {loadingState === LoadingStates.error && <div>
          error loading playlists :(
        </div>}
        {loadingState === LoadingStates.loaded && <div>
          Sorted by<br />
          <ButtonGroup style={{marginBottom: '10px' }} bsSize="small">
            <Button
              onClick={this.sortByTitle}
              active={sortBy === SortModes.default || sortBy === SortModes.title}>
              Title
            </Button>
            <Button
              onClick={this.sortByUsername}
              active={sortBy === SortModes.username}>
              User
            </Button>
            <Button
              onClick={this.sortByAge}
              active={sortBy === SortModes.age}>
              Age
            </Button>
          </ButtonGroup>
          <ScrollableView height={
            this.props.height - 62 /* the sort buttons */
          }>
            <ListGroup>
              {sortedPlaylists.map((playlist) => {
                return (
                  <PlaylistBrowserItem
                    playlist={playlist}
                    open={this.handleOpenPlaylist(playlist.plid)}
                    delete={this.handleDeletePlaylist(playlist.plid)}
                    setPublic={this.handleSetPlaylistPublic(playlist.plid)}
                    key={playlist.plid}
                  />
                );
              })}
            </ListGroup>
          </ScrollableView>
        </div>}
      </div>
    );
  }
}

export default connect(
  (state, dispatch) => {
    return {
      sortedPlaylists: selectSortedPlaylists(state),
      playlistEntities: selectEntitiesPlaylist(state),
      loadingState: selectPlaylistsLoadingState(state),
      sortBy: selectPlaylistSortBy(state),
      sortByReversed: selectPlaylistSortByReversed(state),
    };
  },
  (dispatch) => {
    return {
      requestPlaylistDelete: (playlistId) => dispatch(actionPlaylistDeleteRequested(playlistId)),
      requestPlaylistSetPublic: (playlistId, isPublic) => dispatch(actionPlaylistSetPublicRequested(playlistId, isPublic)),
      openPlaylist: (playlistId) => dispatch(actionPlaylistOpenRequested(playlistId)),
      sortByTitle: () => dispatch(actionPlaylistListSortBy(SortModes.title)),
      sortByAge: () => dispatch(actionPlaylistListSortBy(SortModes.age)),
      sortByUsername: () => dispatch(actionPlaylistListSortBy(SortModes.username)),
    };
  }
)(PlaylistBrowser);

