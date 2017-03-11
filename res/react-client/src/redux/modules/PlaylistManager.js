import {createSelector } from 'reselect';

import {playTrack } from 'redux/modules/Player';
import {
  actionPlaylistAddTrack,
  selectEntitiesPlaylist,
} from 'redux/modules/CherryMusicApi';
import {SERVER_MEDIA_HOST } from 'constants';

const makePlaylistAction = (type) => {
  return (playlistId) => ({type: type, payload: {playlistId: playlistId } });
};
const makePlaylistThunk = (action) => {
  return (playlistId) => (dispatch, getState) => dispatch(action(playlistId));
};
export const ACTIVATE_PLAYLIST = 'redux/cmplaylists/ACTIVATE_PLAYLIST';
export const actionActivatePlaylist = makePlaylistAction(ACTIVATE_PLAYLIST);
export const activatePlaylist = makePlaylistThunk(actionActivatePlaylist);
export const CLOSE_PLAYLIST_TAB = 'redux/cmplaylists/CLOSE_PLAYLIST_TAB';

export const actionClosePlaylistTab = makePlaylistAction(CLOSE_PLAYLIST_TAB);
export const closePlaylistTab = (playlistId) => (dispatch, getState) => {
  const state = getState().playlist;
  dispatch(actionClosePlaylistTab(playlistId));
  // if the currently active playlist is closed, open the next one available:
  if (state.openPlaylistIds.length > 0 && state.activePlaylistId === playlistId){
    dispatch(actionActivatePlaylist(state.openPlaylistIds[0]))
  }
};

export const SET_PLAYING_PLAYLIST = 'redux/cmplaylists/SET_PLAYING_PLAYLIST';
export const actionSetPlayingPlaylist = makePlaylistAction(SET_PLAYING_PLAYLIST);
export const setPlayingPlaylist = makePlaylistThunk(actionSetPlayingPlaylist);

export const PLAY_TRACK_IN_PLAYLIST = 'redux/cmplaylists/PLAY_TRACK_IN_PLAYLIST';

export const PLAY_NEXT_TRACK = 'redux/cmplaylists/PLAY_NEXT_TRACK';
export const actionPlayNextTrack = () => ({type: PLAY_NEXT_TRACK, payload: {} });

export const PLAY_PREVIOUS_TRACK = 'redux/cmplaylists/PLAY_PREVIOUS_TRACK';

export const OPEN_PLAYLIST_TAB = 'redux/cmplaylists/OPEN_PLAYLIST_TAB';
export const actionOpenPlaylistTab = makePlaylistAction(OPEN_PLAYLIST_TAB);

export const CREATE_PLAYLIST_REQUESTED = 'redux/cmplaylists/CREATE_PLAYLIST_REQUESTED';
export const actionCreatePlaylistRequested = () => ({type: CREATE_PLAYLIST_REQUESTED, payload: {} });
export const createPlaylist = () => (dispatch, getState) => dispatch(actionCreatePlaylistRequested());

export const REPLACE_PLAYLIST = 'redux/cmplaylists/REPLACE_PLAYLIST';
export const actionReplacePlaylist = (oldId, newId) => ({type: REPLACE_PLAYLIST, payload: {oldId, newId}});
export const replacePlaylist = (oldId, newId) => (dispatch, getState) => dispatch(actionReplacePlaylist(oldId, newId));

export function playNextTrack () {
  return (dispatch, getState) => {
    dispatch(actionPlayNextTrack());
    const state = _selectOwnState(getState());
    const totalTrackCount = _selectActivePlaylistTrackCount(getState());
    if (totalTrackCount > 0) {
      const playingTrackIdx = _selectPlayingTrackIdx(getState());
      if (totalTrackCount - 1 > playingTrackIdx) {
        dispatch(playTrackInPlaylist(_selectActivePlaylist(getState()), playingTrackIdx + 1));
      }
    }
  };
}
export function playPreviousTrack () {
  return (dispatch, getState) => {
    dispatch({type: PLAY_PREVIOUS_TRACK, payload: {} });
    const totalTrackCount = _selectActivePlaylistTrackCount(getState());
    if (totalTrackCount > 0) {
      const playingTrackIdx = _selectPlayingTrackIdx(getState());
      if (playingTrackIdx > 0) {
        dispatch(playTrackInPlaylist(_selectActivePlaylist(getState()), playingTrackIdx - 1));
      }
    }
  };
}

export function addTrackIdToOpenPlaylist (trackId) {
  return (dispatch, getState) => {
    const activePlaylistId = selectActivePlaylistId(getState());
    dispatch(actionPlaylistAddTrack(activePlaylistId, trackId));
  };
}

export function playTrackInPlaylist (playlist, trackidx) {
  return (dispatch, getState) => {
    dispatch(
      {type: PLAY_TRACK_IN_PLAYLIST, payload: {playlist: playlist, trackidx: trackidx } }
    );
    const trackId = playlist.trackIds[trackidx];
    playTrack(trackId)(dispatch, getState);
  };
}

const _selectOwnState = (state) => state.playlist;
const _selectActivePlaylist = createSelector(
  _selectOwnState, selectEntitiesPlaylist,
  (state, playlistEntities) => {
    return playlistEntities[state.activePlaylistId];
  }
);
const _selectPlayingTrackIdx = (state) => _selectOwnState(state).playingTrackIdx;
const _selectActivePlaylistTrackCount = (state) => {
  const playlist = _selectActivePlaylist(state);
  if (playlist === null) {
    return 0;
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
      openPlaylistIds: [...state.openPlaylistIds, action.payload.playlistId ],
    };
  },
  [CLOSE_PLAYLIST_TAB]: (state, action) => {
    const {playlistId } = action.payload;
    return {
      ...state,
      openPlaylistIds: state.openPlaylistIds.filter((id) => id !== playlistId),
    };
  },
  [ACTIVATE_PLAYLIST]: (state, action) => {
    const activateId = action.payload.playlistId;
    const isOpen = (playlistId) => playlistId === activateId;
    // make sure that the playlist to activate is opened already
    if (!state.openPlaylistIds.some(isOpen)){
      return state;
    }

    return {
      ...state,
      activePlaylistId: activateId,
    };
  },
  [SET_PLAYING_PLAYLIST]: (state, action) => {
    return {
      ...state,
      playingPlaylist: action.payload.playlist,
    };
  },
  [PLAY_TRACK_IN_PLAYLIST]: (state, action) => {
    return {
      ...state,
      playingTrackIdx: action.payload.trackidx,
    };
  },
  [REPLACE_PLAYLIST]: (state, action) => {
    const {oldId, newId} = action.payload;
    return {
      ...state,
      openPlaylistIds: state.openPlaylistIds.map((playlistId) => {
        return oldId === playlistId ? newId : playlistId
      }),
      activePlaylistId: oldId == state.activePlaylistId ? newId : state.activePlaylistId
    }
  }
};

export default function (state = initialState, action) {
  const handler = ACTION_HANDLERS[action.type];
  return handler ? handler(state, action) : state;
}

