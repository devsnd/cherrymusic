import {playTrack} from 'redux/modules/Player';
import {SERVER_MEDIA_HOST} from 'constants';

export const CREATE_PLAYLIST = 'redux/cmplaylists/CREATE_PLAYLIST';
export const CLOSE_PLAYLIST = 'redux/cmplaylists/CLOSE_PLAYLIST';
export const ACTIVATE_PLAYLIST = 'redux/cmplaylists/ACTIVATE_PLAYLIST';
export const SET_PLAYING_PLAYLIST = 'redux/cmplaylists/SET_PLAYING_PLAYLIST';
export const ADD_TRACK_TO_OPEN_PLAYLIST = 'redux/cmplaylists/ADD_TRACK_TO_OPEN_PLAYLIST';
export const PLAY_TRACK_IN_PLAYLIST = 'redux/cmplaylists/PLAY_TRACK_IN_PLAYLIST';
export const PLAY_NEXT_TRACK = 'redux/cmplaylists/PLAY_NEXT_TRACK';
export const PLAY_PREVIOUS_TRACK = 'redux/cmplaylists/PLAY_PREVIOUS_TRACK';

function makeEmptyPlaylist(){
  return {
    name: 'untitled',
    owner: PLAYLIST_OWNER_NOBODY,
    state: playlistStates.new,
    tracks: [],
    randid: Math.floor(Math.random() * 1000000),
  }
}

export const playlistStates = {
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
  dispatch({type: PLAY_NEXT_TRACK, payload: {}});
  const state = _selectOwnState(getState());
  if (
    state.playingPlaylist !== null &&
    state.playingPlaylist.length - 1 > state.playingTrackIdx
  ) {
    playTrackInPlaylist(state.playingPlaylist, state.playingTrackIdx + 1);
  }
}
export function playPreviousTrack () {
  dispatch({type: PLAY_PREVIOUS_TRACK, payload: {}});
  const state = _selectOwnState(getState());
  if (
    state.playingPlaylist !== null &&
    state.playingTrackIdx > 0
  ) {
    playTrackInPlaylist(state.playingPlaylist, state.playingTrackIdx - 1);
  }
}

function actionAddTrackToOpenPlaylist (track) {
  return {type: ADD_TRACK_TO_OPEN_PLAYLIST, payload: {track: track}};
}

export function addTrackToOpenPlaylist (track) {
  return (dispatch, getState) => {
    dispatch(actionAddTrackToOpenPlaylist(track));
  }
}

function actionSetPlayingPlaylist (playlist) {
  return {type: SET_PLAYING_PLAYLIST, payload: {playlist: playlist}};
}

export function setPlayingPlaylist (playlist) {
  return (dispatch, getState) => {
    dispatch(actionSetPlayingPlaylist(playlist));
  }
}

function actionPlayTrackInPlaylist (playlist, trackidx) {
  return {type: PLAY_TRACK_IN_PLAYLIST, payload: {playlist: playlist, trackidx: trackidx}};
}

export function playTrackInPlaylist (playlist, trackidx) {
  return (dispatch, getState) => {
    dispatch(actionPlayTrackInPlaylist(playlist, trackidx));
    const trackUrl = SERVER_MEDIA_HOST + playlist.tracks[trackidx].urlpath;
    const trackLabel = playlist.tracks[trackidx].label;
    playTrack(trackUrl, trackLabel)(dispatch, getState);
  }
}

function _selectOwnState (state) {
  return state.playlist;
}

export function notifyPlaybackEnded (dispatch, getState) {
  playNextTrack(dispatch, getState);
}


const _someEmptyPlaylist = makeEmptyPlaylist();

export const initialState = {
  playlists: [
    _someEmptyPlaylist,
  ],
  activePlaylist: _someEmptyPlaylist,
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
  [ADD_TRACK_TO_OPEN_PLAYLIST]: (state, action) => {
    const previousActivePlaylist = state.activePlaylist;
    const newActivePlaylist = {
      ...state.activePlaylist,
      tracks: [
        ...state.activePlaylist.tracks,
        action.payload.track
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

