// Constants

export const INIT_PLAYER = 'redux/cherrymusic/player/INIT_PLAYER';
export const PLAY_TRACK = 'redux/cherrymusic/player/PLAY_TRACK';
export const TIME_UPDATE = 'redux/cherrymusic/player/TIME_UPDATE';
export const PLAYBACK_ENDED = 'redux/cherrymusic/player/PLAYBACK_ENDED';

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
    audioNode.ended = (evt) => {
      dispatch(actionPlaybackEnded())
    };
    dispatch(actionInit(audioNode));
  }
}

function actionPlaybackEnded () {
  return {type: PLAYBACK_ENDED, payload: {}};
}

function actionTimeUpdate (currentTime, duration) {
  return {
    type: TIME_UPDATE,
    payload: {currentTime: currentTime, duration: duration}
  }
}

function actionPlayTrack (trackUrl, trackLabel) {
  return {type: PLAY_TRACK, payload: {trackUrl: trackUrl, trackLabel: trackLabel}};
}

export function playTrack (trackUrl, trackLabel) {
  return (dispatch, getState) => {
    dispatch(actionPlayTrack(trackUrl, trackLabel));
    const state = getState().player;
    state.audioElement.src = trackUrl;
    state.audioElement.play()
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

