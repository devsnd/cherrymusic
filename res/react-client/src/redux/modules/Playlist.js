import {playTrack} from 'redux/modules/Player';
import {SERVER_MEDIA_HOST} from 'constants';

export const CREATE_PLAYLIST = 'redux/cmplaylists/CREATE_PLAYLIST';
export const CLOSE_PLAYLIST = 'redux/cmplaylists/CLOSE_PLAYLIST';
export const ACTIVATE_PLAYLIST = 'redux/cmplaylists/ACTIVATE_PLAYLIST';
export const SET_PLAYING_PLAYLIST = 'redux/cmplaylists/SET_PLAYING_PLAYLIST';
export const ADD_TRACK_ID_TO_OPEN_PLAYLIST = 'redux/cmplaylists/ADD_TRACK_ID_TO_OPEN_PLAYLIST';
export const PLAY_TRACK_IN_PLAYLIST = 'redux/cmplaylists/PLAY_TRACK_IN_PLAYLIST';
export const PLAY_NEXT_TRACK = 'redux/cmplaylists/PLAY_NEXT_TRACK';
export const PLAY_PREVIOUS_TRACK = 'redux/cmplaylists/PLAY_PREVIOUS_TRACK';
export const OPEN_LOADING_PLAYLIST = 'redux/cmplaylists/OPEN_LOADING_PLAYLIST';

function makeEmptyPlaylist () {
  return {
    name: 'untitled',
    owner: PLAYLIST_OWNER_NOBODY,
    state: playlistStates.new,
    trackIds: [],
    randid: Math.floor(Math.random() * 1000000),
  }
}

function makeLoadingPlaylist () {
  playlist = makeEmptyPlaylist ();
  playlist.state = playlistStates.loading;
  playlist.name = 'loading';
  return playlist;
}

export const playlistStates = {
  loading: 'loading',
  new: 'new',
  saving: 'saving',
  saved: 'saved',
};

// placeholder for playlists that do not belong to anybody
// owner is determined by the server on save.
export const PLAYLIST_OWNER_NOBODY = {};

function actionActivatePlaylist (playlist) {
  return {type: ACTIVATE_PLAYLIST, payload: {playlist: playlist}};
}

export function activatePlaylist (playlist) {
  return (dispatch, getState) => {
    dispatch(actionActivatePlaylist(playlist));
  }
}

function actionClosePlaylist (playlist) {
  return {type: CLOSE_PLAYLIST, payload: {playlist: playlist}};
}

export function closePlaylist (playlist) {
  return (dispatch, getstate) => {
    dispatch(actionClosePlaylist(playlist))
  }
}

function actionCreatePlaylist () {
  return {type: CREATE_PLAYLIST, payload: {}};
}

export function createPlaylist (activate = false) {
  return (dispatch, getState) => {
    dispatch(actionCreatePlaylist());
    if (activate) {
      const playlists = getState().playlist.playlists;
      dispatch(actionActivatePlaylist(playlists[playlists.length - 1]));
    }
  }
}

export function playNextTrack () {
  return (dispatch, getState) => {
    dispatch({type: PLAY_NEXT_TRACK, payload: {}});
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

export function setPlayingPlaylist (playlist) {
  return (dispatch, getState) => {
    dispatch({type: SET_PLAYING_PLAYLIST, payload: {playlist: playlist}});
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
const _selectPlayingPlaylist = (state) => _selectOwnState(state).playingPlaylist;
const _selectPlayingTrackIdx = (state) => _selectOwnState(state).playingTrackIdx;
const _selectPlayingPlaylistTrackCount = (state) => {
  const playlist = _selectPlayingPlaylist(state);
  if (playlist === null) {
    return 0
  }
  return playlist.trackIds.length;
};


export function notifyPlaybackEnded (dispatch, getState) {
  dispatch(playNextTrack());
}
const _initialEmptyPlaylist = makeEmptyPlaylist();

export const initialState = {
  playlists: [
    _initialEmptyPlaylist,
  ],
  activePlaylist: _initialEmptyPlaylist,
  playingPlaylist: null,
  playingTrackIdx: null,
};

// Action HANDLERS
const ACTION_HANDLERS = {
  [CREATE_PLAYLIST]: (state, action) => {
    return {
      ...state,
      playlists: [
        ...state.playlists,
        makeEmptyPlaylist()
      ]
    };
  },
  [CLOSE_PLAYLIST]: (state, action) => {
    const playlist = action.payload.playlist;
    return {
      ...state,
      playlists: state.playlists.filter(
        (iterPlaylist) => { return iterPlaylist !== playlist }
      )
    };
  },
  [ACTIVATE_PLAYLIST]: (state, action) => {
    return {
      ...state,
      activePlaylist: action.payload.playlist
    }
  },
  [ADD_TRACK_ID_TO_OPEN_PLAYLIST]: (state, action) => {
    const previousActivePlaylist = state.activePlaylist;
    const newActivePlaylist = {
      ...state.activePlaylist,
      trackIds: [
        ...state.activePlaylist.trackIds,
        action.payload.trackId
      ]
    };
    return {
      ...state,
      activePlaylist: newActivePlaylist,
      playlists: state.playlists.map((pl) => {
        // replace only the active playlist, leave all others in place:
        return previousActivePlaylist === pl ? newActivePlaylist : pl
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

