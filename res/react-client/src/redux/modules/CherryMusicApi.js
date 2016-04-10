import {API_ENDPOINT_LIST_DIRECTORY, API_ENDPOINT_SEARCH} from 'constants';
import {legacyAPICall} from 'utils/legacyApi';
import {LOG_IN_SUCCESS} from 'redux/modules/Auth';

export const DIRECTORY_LOADING = 'redux/cherrymusicapi/directory_loading';
export const DIRECTORY_LOADED = 'redux/cherrymusicapi/directory_loaded';
export const DIRECTORY_LOAD_ERROR = 'redux/cherrymusicapi/directory_load_error';

export const LoadingStates = {
  idle: 'idle',
  loading: 'loading',
  loaded: 'loaded',
  error: 'error',
};

export function loadDirectory (path) {
  return (dispatch, getState) => {
    const {authtoken} = getState().api; // there must be a cleaner way!
    dispatch(actionDirectoryLoading(path));
    dispatch(actionDirectoryLoading(path));
    if(typeof path === 'undefined'){
      path = '';
    }
    legacyAPICall(API_ENDPOINT_LIST_DIRECTORY, {'directory': path}, authtoken).then(
      (data) => {
        const collections = data.filter((elem) => { return elem.type === 'dir'; });
        const tracks = data.filter((elem) => { return elem.type !== 'dir'; });
        dispatch(actionDirectoryLoaded(path, collections, tracks));
      },
      (error) => { console.log(error) }
    )
  }
}

export function search (searchterm) {
  return (dispatch, getState) => {
    const {authtoken} = getState().api; // there must be a cleaner way!
    dispatch(actionDirectoryLoading(searchterm));
    legacyAPICall(API_ENDPOINT_SEARCH, {'searchstring': searchterm}, authtoken).then(
      (data) => {
        const collections = data.filter((elem) => {
          return elem.type === 'dir';
        });
        const tracks = data.filter((elem) => {
          return elem.type !== 'dir';
        });
        dispatch(actionDirectoryLoaded(
          'Search: ' + searchterm,
          collections,
          tracks
        ));
      },
      (error) => {
        console.log(error)
      }
    );
  }
}

function actionDirectoryLoading(path){
  return {type: DIRECTORY_LOADING, payload: {path: path}};
}

function actionDirectoryLoaded(path, collections, tracks){
  return {
    type: DIRECTORY_LOADED,
    payload: {
      path: path,
      collections: collections,
      tracks: tracks
    }
  };
}

export const initialState = {
  authtoken: null,
  state: LoadingStates.idle,
  path: null,
  collections: [],
  tracks: [],
};

// Action HANDLERS
const ACTION_HANDLERS = {
  [DIRECTORY_LOADING]: (state, action) => {
    const {path} = action.payload;
    return {
      ...state,
      state: LoadingStates.loading,
      path: path,
      collections: [],
      tracks: [],
    }
  },
  [DIRECTORY_LOADED]: (state, action) => {
    const {path, collections, tracks} = action.payload;
    return {
      ...state,
      state: LoadingStates.loaded,
      collections: collections,
      tracks: tracks,
    }
  },
  [DIRECTORY_LOAD_ERROR]: (state, action) => {
    return {
      ...state,
      browser: {
        ...state.browser,
        collections: {
          state: LoadingStates.error,
          data: [],
        }
      }
    }
  },
  [LOG_IN_SUCCESS]: (state, action) => {
    return {
      ...state,
      authtoken: action.payload.authtoken
    }
  }
};

export default function (state = initialState, action) {
  const handler = ACTION_HANDLERS[action.type];
  return handler ? handler(state, action) : state;
}

