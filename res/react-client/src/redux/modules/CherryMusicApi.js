import { normalize, Schema, arrayOf } from 'normalizr';

import {API_ENDPOINT_LIST_DIRECTORY, API_ENDPOINT_SEARCH} from 'constants';
import {legacyAPICall} from 'utils/legacyApi';
import {LOG_IN_SUCCESS} from 'redux/modules/Auth';

export const getAuthToken = (state) => state.api.authtoken;

export const DIRECTORY_LOADING = 'redux/cherrymusicapi/directory_loading';
export const DIRECTORY_LOADED = 'redux/cherrymusicapi/directory_loaded';
export const DIRECTORY_LOAD_ERROR = 'redux/cherrymusicapi/directory_load_error';

const trackSchema = new Schema('track', { idAttribute: 'path' });
const collectionSchema = new Schema('collection', { idAttribute: 'path' });

export const LoadingStates = {
  idle: 'idle',
  loading: 'loading',
  loaded: 'loaded',
  error: 'error',
};

export function loadDirectory (path) {
  return (dispatch, getState) => {
    const authtoken = getAuthToken(getState());
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
    const authtoken = getAuthToken(getState());
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
  entities: {},
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
    const normCollection = normalize(collections, arrayOf(collectionSchema));
    const normTracks = normalize(tracks, arrayOf(trackSchema));
    const results = {
      collections: normCollection.result,
      tracks: normTracks.result,
    };
    const receivedEntities = {
      ...normCollection.entities,
      ...normTracks.entities,
    };
    const newEntities = {...state.entities};
    for (let model of Object.keys(receivedEntities)) {
      if (typeof newEntities[model] === 'undefined') {
        newEntities[model] = receivedEntities[model];
      } else {
        newEntities[model] = {...newEntities[model], ...receivedEntities[model]};
      }
    }

    return {
      ...state,
      state: LoadingStates.loaded,
      entities: newEntities,
      collections: normCollection.result,
      tracks: normTracks.result,
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

