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

import {
  selectSortedPlaylists,
  selectPlaylistsLoadingState,
  selectPlaylistIds,
  selectPlaylistSortBy,
  selectPlaylistSortByReversed,
  PlaylistSortModes as SortModes,
  actionPlaylistListSortBy,
  LoadingStates,
} from 'redux/modules/CherryMusicApi';
import Age from 'components/Age/Age'

class PlaylistBrowser extends React.Component {
  static propTypes = {

  };

  constructor (props) {
    super(props);
    this.sortByTitle = () => {
      this.props.dispatch(actionPlaylistListSortBy(SortModes.title));
    };
    this.sortByAge = () => {
      this.props.dispatch(actionPlaylistListSortBy(SortModes.age));
    };
    this.sortByUsername = () => {
      this.props.dispatch(actionPlaylistListSortBy(SortModes.username));
    };
  }

  handleSetPlaylistPublic (evt) {

  }

  handleOpenPlaylist (playlistId) {

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
          <ButtonGroup style={{marginBottom: '10px'}}>
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
          <ListGroup>
            {sortedPlaylists.map((playlist) => {
              const playlistId = playlist.plid;
              return (
                <ListGroupItem
                  onClick={() => this.handleOpenPlaylist(playlistId)}
                  key={playlistId}
                >
                  {playlist.title}
                  <span style={{float: 'right'}}>
                    <Age seconds={playlist.age} />
                  </span>
                  {playlist.owner && <span>
                    {playlist.public &&
                      <Label bsStyle="success">
                        public&nbsp;<input
                          type="checkbox"
                          checked
                          onChange={this.handleSetPlaylistPublic}
                        />
                      </Label>
                    }
                    {!playlist.public &&
                      <Label bsStyle="default">
                        public&nbsp;<input
                          type="checkbox"
                          onChange={this.handleSetPlaylistPublic}
                        />
                      </Label>
                    }
                  </span>}
                  <Username name={playlist.username} />
                </ListGroupItem>
              );
            })}
          </ListGroup>
        </div>}
      </div>
    )
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
      dispatch: dispatch
    };
  }
)(PlaylistBrowser);

