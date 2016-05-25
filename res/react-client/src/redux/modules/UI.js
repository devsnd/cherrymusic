// this reducer covers all the state needed only for the UI to render nicely.

export const SET_VIEW = 'redux/cherrymusic/SET_VIEW';

export const ViewStates = {
  motd: 'motd',
  browser: 'browser',
  playlists: 'playlists',
};

export const actionSetView = (viewState) => {return {type: SET_VIEW, payload: {viewState: viewState}}};

export function setBrowserView () {
  return (dispatch, getState) => dispatch(actionSetView(ViewStates.browser));
}
export function setPlaylistView () {
  return (dispatch, getState) => dispatch(actionSetView(ViewStates.playlists));
}

export const initialState = {
  viewState: ViewStates.motd,
};

const ACTION_HANDLERS = {
   [SET_VIEW]: (state, action) => {
     return {
       ...state,
       viewState: action.payload.viewState,
     };
   }
};

export default function (state = initialState, action) {
  const handler = ACTION_HANDLERS[action.type];
  return handler ? handler(state, action) : state;
}

