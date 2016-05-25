// Constants
import {notifyPlaybackEnded} from 'redux/modules/Playlist';
import {SERVER_MEDIA_HOST} from 'constants';
import {selectEntityTrackById} from 'redux/modules/CherryMusicApi';

export const INIT_PLAYER = 'redux/cherrymusic/player/INIT_PLAYER';
export const PLAY_TRACK = 'redux/cherrymusic/player/PLAY_TRACK';
export const RESUME_TRACK = 'redux/cherrymusic/player/RESUME_TRACK';
export const PAUSE_TRACK = 'redux/cherrymusic/player/PAUSE_TRACK';
export const TIME_UPDATE = 'redux/cherrymusic/player/TIME_UPDATE';
export const PLAYBACK_ENDED = 'redux/cherrymusic/player/PLAYBACK_ENDED';
export const SEEK = 'redux/cherrymusic/player/SEEK';

function actionInit (audioElement) {
  return {type: INIT_PLAYER, payload: {audioElement: audioElement}};
}

export function initPlayer (domElement) {
  return (dispatch, getState) => {
    var audioNode = document.createElement("audio");
    domElement.appendChild(audioNode);
    audioNode.ontimeupdate = (evt) => {
      dispatch(actionTimeUpdate(evt.target.currentTime, evt.target.duration));
    };
    audioNode.onended = (evt) => {
      notifyPlaybackEnded(dispatch, getState);
    };
    audioNode.onpause = (evt) => {
      // after calling pause() on the audio element, it still might fire a
      // timeupdate, which will reset the state to playing.
      // listening to the <audio> pause event makes sure we stay in the paused
      // state.
      dispatch(actionPause());
    };
    dispatch(actionInit(audioNode));
  }
}

function actionPlaybackEnded () {
  return {type: PLAYBACK_ENDED, payload: {}};
}

function actionPause () {
  return {type: PAUSE_TRACK, payload: {}};
}

function actionResume () {
  return {type: RESUME_TRACK, payload: {}};
}

function actionTimeUpdate (currentTime, duration) {
  return {
    type: TIME_UPDATE,
    payload: {currentTime: currentTime, duration: duration}
  }
}

const _selectOwnState = (state) => state.player;
const _selectAudioElement = (state) => _selectOwnState(state).audioElement;
const _selectDuration = (state) => _selectOwnState(state).duration;

function actionSeek (positionSecs) {
  return {type: SEEK, payload: {positionSecs: positionSecs}}
}

export function seek (percentage) {
  return (dispatch, getState) => {
    const state = getState();
    const newPositionSecs = _selectDuration(state) * (percentage / 100);
    const audioElement = _selectAudioElement(state);
    audioElement.currentTime = newPositionSecs;
    audioElement.play();
    dispatch(actionSeek (newPositionSecs));
  }
}

export function playTrack (trackId) {
  return (dispatch, getState) => {
    const state = getState();
    const audioElement = _selectAudioElement(state);
    const track = selectEntityTrackById(state)(trackId);
    dispatch({type: PLAY_TRACK, payload: {trackId: trackId}});
    audioElement.src = SERVER_MEDIA_HOST + track.urlpath;
    audioElement.play()
  }
}

export function pause () {
  return (dispatch, getState) => {
    const {player} = getState();
    dispatch(actionPause());
    player.audioElement.pause();
  }
}

export function resume () {
  return (dispatch, getState) => {
    const {player} = getState();
    dispatch(actionResume());
    player.audioElement.play();
  }
}

export const playerStates = {
  uninitialized: 'uninitialized',
  ready: 'ready',
  startingPlay: 'startingPlay',
  playing: 'playing',
  error: 'error',
};

export const initialState = {
  state: playerStates.uninitialized,
  audioElement: null,
  trackUrl: null,
  duration: null,
  currentTime: null,
  trackLabel: '',
  percentage: 0,
};

// Action HANDLERS
const ACTION_HANDLERS = {
  [INIT_PLAYER]: (state, action) => {
    return {
      ...state,
      state: playerStates.ready,
      audioElement: action.payload.audioElement,
    }
  },
  [PLAY_TRACK]: (state, action) => {
    return {
      ...state,
      state: playerStates.startingPlay,
      trackUrl: action.payload.trackUrl,
      trackLabel: action.payload.trackLabel,
    }
  },
  [PAUSE_TRACK]: (state, action) => {
    return {
      ...state,
      state: playerStates.paused,
    }
  },
  [RESUME_TRACK]: (state, action) => {
    return {
      ...state,
      state: playerStates.startingPlay
    }
  },
  [SEEK]: (state, action) => {
    const {positionSecs, duration} = action.payload;
    const percentage = (positionSecs / duration) * 100;
    return {
      ...state,
      state: playerStates.startingPlay,
      currentTime: positionSecs,
      percentage: percentage,
    }
  },
  [TIME_UPDATE]: (state, action) => {
    let percentage = 0;
    if (action.payload.duration) {
      percentage = (action.payload.currentTime / action.payload.duration) * 100;
    }
    return {
      ...state,
      state: playerStates.playing,
      duration: action.payload.duration,
      currentTime: action.payload.currentTime,
      percentage: percentage,
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

