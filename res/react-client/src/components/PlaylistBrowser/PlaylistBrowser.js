import React, {PropTypes} from 'react';
import { bindActionCreators } from 'redux'
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
import Age from 'components/Age/Age'

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
  }

  handleSetPlaylistPublic (evt) {

  }

  render () {
    const {sortedPlaylists, loadingState, sortBy, sortByReversed} = this.props;
    return (
      <div>
        {loadingState === LoadingStates.loading && <div>
          loading...
        </div>}
        {loadingState === LoadingStates.error && <div>
          error loading playlists :(
        </div>}
        {loadingState === LoadingStates.loaded && <div>
          Sorted by<br />
          <ButtonGroup style={{marginBottom: '10px'}} bsSize="small">
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
                const playlistId = playlist.plid;
                const inputChecked = playlist.public ? {checked: true} : {};
                return (
                  <ListGroupItem
                    onClick={() => this.props.openPlaylist(playlistId)}
                    key={playlistId}
                  >
                    {playlist.title}
                    <span style={{float: 'right'}}>
                      <Age seconds={playlist.age} />
                    </span>
                    {playlist.owner && <span>
                      <Label
                        bsStyle={playlist.public ? 'success' : 'default'}
                        style={{float: 'right'}}
                      >
                          public&nbsp;<input
                          type="checkbox"
                          {...inputChecked}
                          onChange={this.handleSetPlaylistPublic}
                        />
                      </Label>
                    </span>}
                    <Username name={playlist.username} />
                  </ListGroupItem>
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
      loadingState: selectPlaylistsLoadingState(state),
      sortBy: selectPlaylistSortBy(state),
      sortByReversed: selectPlaylistSortByReversed(state),
    };
  },
  (dispatch) => {
    return {
      openPlaylist: (playlistId) => dispatch(actionPlaylistOpenRequested(playlistId)),
      sortByTitle: () => dispatch(actionPlaylistListSortBy(SortModes.title)),
      sortByAge: () => dispatch(actionPlaylistListSortBy(SortModes.age)),
      sortByUsername: () => dispatch(actionPlaylistListSortBy(SortModes.username)),
    };
  }
)(PlaylistBrowser);

