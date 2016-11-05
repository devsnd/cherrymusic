import {playTrack} from 'redux/modules/Player';
import {SERVER_MEDIA_HOST} from 'constants';

const makePlaylistAction = (type) => {
  return (playlistId) => ({type: type, payload: {playlistId: playlistId}});
};
const makePlaylistThunk = (action) => {
  return (playlistId) => (dispatch, getState) => dispatch(action(playlistId));
};

export const CREATE_PLAYLIST = 'redux/cmplaylists/CREATE_PLAYLIST';
export const actionCreatePlaylist = () => ({type: CREATE_PLAYLIST, payload: {}});
export const createPlaylist = (activate = false) => (dispatch, getState) => {
  dispatch(actionCreatePlaylist());
  if (activate) {
    const playlists = getState().playlist.playlists;
    dispatch(actionActivatePlaylist(playlists[playlists.length - 1]));
  }
};

export const CLOSE_PLAYLIST_TAB = 'redux/cmplaylists/CLOSE_PLAYLIST_TAB';
export const actionClosePlaylistTab = makePlaylistAction(CLOSE_PLAYLIST_TAB);
export const closePlaylistTab = makePlaylistThunk(actionClosePlaylistTab);

export const ACTIVATE_PLAYLIST = 'redux/cmplaylists/ACTIVATE_PLAYLIST';
export const actionActivatePlaylist = makePlaylistAction(ACTIVATE_PLAYLIST);
export const activatePlaylist = makePlaylistThunk(actionActivatePlaylist);

export const SET_PLAYING_PLAYLIST = 'redux/cmplaylists/SET_PLAYING_PLAYLIST';
export const actionSetPlayingPlaylist = makePlaylistAction(SET_PLAYING_PLAYLIST);
export const setPlayingPlaylist = makePlaylistThunk(actionSetPlayingPlaylist);

export const ADD_TRACK_ID_TO_OPEN_PLAYLIST = 'redux/cmplaylists/ADD_TRACK_ID_TO_OPEN_PLAYLIST';
export const PLAY_TRACK_IN_PLAYLIST = 'redux/cmplaylists/PLAY_TRACK_IN_PLAYLIST';

export const PLAY_NEXT_TRACK = 'redux/cmplaylists/PLAY_NEXT_TRACK';
export const actionPlayNextTrack = () => ({type: PLAY_NEXT_TRACK, payload: {}});

export const PLAY_PREVIOUS_TRACK = 'redux/cmplaylists/PLAY_PREVIOUS_TRACK';

export const OPEN_PLAYLIST_TAB = 'redux/cmplaylists/OPEN_PLAYLIST_TAB';
export const actionOpenPlaylistTab = makePlaylistAction(OPEN_PLAYLIST_TAB);

export const CREATE_PLAYLIST_REQUESTED = 'redux/cmplaylists/CREATE_PLAYLIST_REQUESTED';
export const actionCreatePlaylistRequested = () => ({type: CREATE_PLAYLIST_REQUESTED, payload: {}});

export function playNextTrack () {
  return (dispatch, getState) => {
    dispatch(actionPlayNextTrack());
    const state = _selectOwnState(getState());
    const totalTrackCount = _selectPlayingPlaylistTrackCount(getState());
    if (totalTrackCount > 0) {
      const playingTrackIdx = _selectPlayingTrackIdx(getState());
      if (totalTrackCount - 1 > playingTrackIdx) {
        dispatch(playTrackInPlaylist(_selectPlayingPlaylist(getState()), playingTrackIdx + 1));
      }
    }
  }
}
export function playPreviousTrack () {
  return (dispatch, getState) => {
    dispatch({type: PLAY_PREVIOUS_TRACK, payload: {}});
    const totalTrackCount = _selectPlayingPlaylistTrackCount(getState());
    if (totalTrackCount > 0) {
      const playingTrackIdx = _selectPlayingTrackIdx(getState());
      if (playingTrackIdx > 0) {
        dispatch(playTrackInPlaylist(_selectPlayingPlaylist(getState()), playingTrackIdx - 1));
      }
    }
  }
}

export function addTrackIdToOpenPlaylist (trackId) {
  return (dispatch, getState) => {
    dispatch(
      {type: ADD_TRACK_ID_TO_OPEN_PLAYLIST, payload: {trackId: trackId}}
    );
  }
}

export function playTrackInPlaylist (playlist, trackidx) {
  return (dispatch, getState) => {
    dispatch(
      {type: PLAY_TRACK_IN_PLAYLIST, payload: {playlist: playlist, trackidx: trackidx}}
    );
    const trackId = playlist.trackIds[trackidx];
    playTrack(trackId)(dispatch, getState);
  }
}

const _selectOwnState = (state) => state.playlist;
const _selectPlaylists = (state) => _selectOwnState(state).playlists;
const _selectPlayingPlaylist = (state) => _selectOwnState(state).playingPlaylist;
const _selectPlayingTrackIdx = (state) => _selectOwnState(state).playingTrackIdx;
const _selectPlayingPlaylistTrackCount = (state) => {
  const playlist = _selectPlayingPlaylist(state);
  if (playlist === null) {
    return 0
  }
  return playlist.trackIds.length;
};

export const selectActivePlaylistId = (state) => _selectOwnState(state).activePlaylistId;

export function notifyPlaybackEnded (dispatch, getState) {
  dispatch(playNextTrack());
}

export const initialState = {
  openPlaylistIds: [],
  activePlaylistId: null,
  playingPlaylist: null,
  playingTrackIdx: null,
};

// Action HANDLERS
const ACTION_HANDLERS = {
  [OPEN_PLAYLIST_TAB]: (state, action) => {
    return {
      ...state,
      openPlaylistIds: [...state.openPlaylistIds, action.payload.playlistId]
    }
  },
  [CLOSE_PLAYLIST_TAB]: (state, action) => {
    const {playlistId} = action.payload;
    return {
      ...state,
      openPlaylistIds: state.openPlaylistIds.filter((id) => id !== playlistId)
    };
  },
  [ACTIVATE_PLAYLIST]: (state, action) => {
    return {
      ...state,
      activePlaylistId: action.payload.playlistId
    }
  },
  [ADD_TRACK_ID_TO_OPEN_PLAYLIST]: (state, action) => {
    // find the correct playlist and create a modified verion that
    // includes the track
    const {playlistId, trackId} = action.payload;
    for (const playlist of _selectPlaylists(state)) {
      if (playlist.id == playlistId) {
        // found the correct playlist
        const modifiedPlaylist = {
          ...playlist,
          trackIds: [
            ...playlist.trackIds,
            trackId
          ]
        }
      }
    }

    return {
      ...state,
      playlists: state.playlists.map((pl) => {
        // replace only the active playlist, leave all others in place:
        return playlistId === pl.id ? modifiedPlaylist : pl
      })
    }
  },
  [SET_PLAYING_PLAYLIST]: (state, action) => {
    return {
      ...state,
      playingPlaylist: action.payload.playlist,
    }
  },
  [PLAY_TRACK_IN_PLAYLIST]: (state, action) => {
    return {
      ...state,
      playingTrackIdx: action.payload.trackidx
    }
  }
  // SOME_ACTION: (state, action) => {
  //   return state;
  // }
};

export default function (state = initialState, action) {
  const handler = ACTION_HANDLERS[action.type];
  return handler ? handler(state, action) : state;
}

