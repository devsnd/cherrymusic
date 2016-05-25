import React, {PropTypes} from 'react';
import { bindActionCreators } from 'redux'
import { connect } from 'react-redux';

import {ListGroup, ListGroupItem, Label, Badge} from 'react-bootstrap';
import Username from 'components/Username/Username';


import {
  selectEntitiesPlaylist,
  selectPlaylistsLoadingState,
  selectPlaylistIds,
  LoadingStates,
} from 'redux/modules/CherryMusicApi';
import Age from 'components/Age/Age'

class PlaylistBrowser extends React.Component {
  static propTypes = {

  };

  handleSetPlaylistPublic (evt) {
    console.log(evt);
    alert('not implemented :(');
  }

  handleOpenPlaylist (playlistId) {

  }

  constructor (props) {
    super(props);
    this.state = {};
  }

  render () {
    const {playlistEntities, playlistIds, loadingState} = this.props;
    return (
      <div>
        {loadingState === LoadingStates.loading && <div>
          loading...
        </div>}
        {loadingState === LoadingStates.error && <div>
          error loading playlists :(
        </div>}
        {loadingState === LoadingStates.loaded && <div>
          <ListGroup>
            {playlistIds.map((playlistId) => {
              const playlist = playlistEntities[playlistId];
              return (
                <ListGroupItem
                  onClick={() => this.handleOpenPlaylist(playlistId)}
                  key={playlistId}
                >
                  {playlist.title}
                  <Age seconds={playlist.age} />
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
      playlistEntities: selectEntitiesPlaylist(state),
      playlistIds: selectPlaylistIds(state),
      loadingState: selectPlaylistsLoadingState(state),
    };
  },
  (dispatch) => {
    return {

    };
  }
)(PlaylistBrowser);

