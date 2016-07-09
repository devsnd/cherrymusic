import { normalize, Schema, arrayOf } from 'normalizr';

import {
  API_ENDPOINT_LIST_DIRECTORY,
  API_ENDPOINT_SEARCH,
  API_ENDPOINT_TRACK_METADATA,
  API_ENDPOINT_PLAYLIST_LIST,
  API_ENDPOINT_PLAYLIST_DETAIL,
} from 'constants';
import {legacyAPICall} from 'utils/legacyApi';
import {LOG_IN_SUCCESS} from 'redux/modules/Auth';
import updateHelper from 'react-addons-update';
import { createSelector } from 'reselect';

export const getAuthToken = (state) => state.api.authtoken;

export const PLAYLIST_LIST_REQUESTED = 'redux/cherrymusicapi/PLAYLIST_LIST_REQUESTED';
export const PLAYLIST_LIST_LOADED = 'redux/cherrymusicapi/PLAYLIST_LIST_LOADED';
export const PLAYLIST_LIST_LOAD_ERROR = 'redux/cherrymusicapi/PLAYLIST_LIST_LOAD_ERROR';
export const PLAYLIST_LIST_SORT_BY = 'redux/cherrymusicapi/PLAYLIST_LIST_SORT_BY';

export const PLAYLIST_OPEN_REQUESTED = 'redux/cherrymusicapi/PLAYLIST_OPEN_REQUESTED';
export const PLAYLIST_DETAIL_LOADING = 'redux/cherrymusicapi/PLAYLIST_DETAIL_LOADING';
export const PLAYLIST_DETAIL_LOADED = 'redux/cherrymusicapi/PLAYLIST_DETAIL_LOADED';
export const PLAYLIST_DETAIL_LOAD_ERROR = 'redux/cherrymusicapi/PLAYLIST_DETAIL_LOAD_ERROR';


export const DIRECTORY_LOADING = 'redux/cherrymusicapi/directory_loading';
export const DIRECTORY_LOADED = 'redux/cherrymusicapi/directory_loaded';
export const DIRECTORY_LOAD_ERROR = 'redux/cherrymusicapi/directory_load_error';

export const METADATA_LOAD_ENQUEUE = 'redux/cherrymusicapi/metadata_load_enqueue';
export const METADATA_LOAD = 'redux/cherrymusicapi/metadata_load';
export const METADATA_LOADING = 'redux/cherrymusicapi/metadata_loading';
export const METADATA_LOADED = 'redux/cherrymusicapi/metadata_loaded';
export const METADATA_LOAD_ERROR = 'redux/cherrymusicapi/metadata_load_error';

const trackSchema = new Schema('track', { idAttribute: 'path' });
const collectionSchema = new Schema('collection', { idAttribute: 'path' });
const playlistSchema = new Schema('playlist', { idAttribute: 'plid' });

export const LoadingStates = {
  idle: 'idle',
  loading: 'loading',
  loaded: 'loaded',
  error: 'error',
};

export const MetaDataLoadingStates = {
  idle: 'idle',
  loading: 'loading',
  loaded: 'loaded',
  error: 'error',
};

export const PlaylistSortModes = {
  default: 'default',
  title: 'title',
  username: 'username',
  age: 'age',
};

export function selectTrackMetaDataLoadingState (track) {
  if (typeof track.metadata === 'undefined') {
    return MetaDataLoadingStates.idle;
  }
  return track.metadataLoadingState;
}

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

export function fetchPlaylistList (getState, sortby='default', filterby) {
  const params = {sortby: sortby};
  if (typeof filterby !== 'undefined') {
    params.filterby = filterby;
  }
  const authtoken = getAuthToken(getState());
  return legacyAPICall(API_ENDPOINT_PLAYLIST_LIST, params, authtoken);
}

export function fetchPlaylistDetail (getState, playlistId) {
  const authtoken = getAuthToken(getState());
  return legacyAPICall(
    API_ENDPOINT_PLAYLIST_DETAIL,
    {playlistid: playlistId},
    authtoken
  );
}

export function isTrackVisible (apistate, track) {
  const collections = apistate.entities[collectionSchema.getKey()];
  // check if the track is visible inside the browser (the browser always
  // displays the api.collections)
  return collections.indexOf(trackSchema.getId(track)) !== -1;
}

export function fetchTrackMetaData (track) {
  return legacyAPICall(API_ENDPOINT_TRACK_METADATA, {path: track.path});
}

export function actionMetaDataLoading (track, metadata) {
  return {type: METADATA_LOADING, payload: {track: track}};
}

export function actionMetaDataLoaded (track, metadata) {
  return {type: METADATA_LOADED, payload: {track: track, metadata: metadata}};
}

export function actionMetaDataLoadError (track) {
  return {type: METADATA_LOAD_ERROR, payload: {track: track}};
}

export function actionPlaylistOpenRequested (playlistId) {
  return {type: PLAYLIST_OPEN_REQUESTED, payload: {playlistId: playlistId}}
}

export function loadTrackMetaData (track) {
  return (dispatch, getState) => {
    const state = selectTrackMetaDataLoadingState(track);
    if (state === MetaDataLoadingStates.idle) {
      dispatch({type: METADATA_LOADING, payload: {track: track}});
      legacyAPICall(API_ENDPOINT_TRACK_METADATA, {path: track.path}).then(
        (data) => {
          const metadata = data;
          dispatch({type: METADATA_LOADED, payload: {track: track, metadata: data}});
        },
        (error) => {
          console.log(error);
          dispatch({type: METADATA_LOAD_ERROR, payload: {track: track}});
        }
      )
    }
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

export function actionPlaylistListRequested (sortby, filterby) {
  return {type: PLAYLIST_LIST_REQUESTED, payload: {sortby: sortby, filterby: filterby}};
}

export function actionPlaylistListLoadError () {
  return {type: PLAYLIST_LIST_LOAD_ERROR, payload: {}};
}

export function actionPlaylistListLoaded (playlists, sortby, filterby) {
  return {
    type: PLAYLIST_LIST_LOADED,
    payload: {
      playlists: playlists,
      sortby: sortby,
      filterby: filterby,
    }
  }
}

export function actionPlaylistListSortBy (sortMode) {
  return {type: PLAYLIST_LIST_SORT_BY, payload: {sortBy: sortMode}};
}

export function selectAPI (state) {
  return state.api;
}

export function selectEntitiesTrack (state) {
  return selectAPI(state).entities.track;
}

export function selectEntityTrackById (state) {
  return (trackId) =>  selectEntitiesTrack(state)[trackId];
}

export function selectEntitiesTrackByNewTrack (state) {
  // returns a selector bound to the state to find tracks using their id.
  return (newTrack) => selectEntityTrackById(trackSchema.getId(newTrack));
}

export function selectEntitiesPlaylist (state) {
  return selectAPI(state).entities.playlist;
}

export const selectSortedPlaylists = createSelector(
  selectEntitiesPlaylist,
  selectPlaylistSortBy,
  selectPlaylistSortByReversed,
  (playlistEntities, sortBy, reversed) => {
    const sortedPlaylists = [];
    Object.keys(playlistEntities).map((plid) => {
      sortedPlaylists.push(playlistEntities[plid]);
    });
    const sortKeyFunc = {
      [PlaylistSortModes.default]: (pl) => pl.created,
      [PlaylistSortModes.age]: (pl) => pl.created,
      [PlaylistSortModes.username]: (pl) => pl.username.toLowerCase().trim(),
      [PlaylistSortModes.title]: (pl) => pl.title.toLowerCase().trim(),
    }[sortBy];
    sortedPlaylists.sort((playlistA, playlistB) => {
      const aVal = sortKeyFunc(playlistA);
      const bVal = sortKeyFunc(playlistB);
      if (aVal === bVal) {
        return 0
      }
      if (reversed) {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
    return sortedPlaylists;
  }
);

export function selectPlaylistIds (state) {
  return selectAPI(state).playlists;
}

export function selectPlaylistsLoadingState (state) {
  return selectAPI(state).playlistsLoadingState;
}

export function selectPlaylistSortBy (state) {
  return selectAPI(state).playlistSortBy;
}

export function selectPlaylistSortByReversed (state) {
  return selectAPI(state).playlistSortByReversed;
}

export const initialState = {
  authtoken: null,
  state: LoadingStates.idle,
  entities: {
    [trackSchema.getKey()]: {},
    [collectionSchema.getKey()]: {},
    [playlistSchema.getKey()]: {},
  },
  path: null,
  collections: [],
  tracks: [],

  playlistsLoadingState: LoadingStates.idle,
  playlistFilterBy: '',
  playlistSortBy: PlaylistSortModes.default,
  playlists: [],
};

export function selectAPIState (state) {
  return state.api;
}

// Action HANDLERS
const ACTION_HANDLERS = {
  [METADATA_LOAD_ENQUEUE]: (state, action) => {
    const {track} = action.payload;
    return updateHelper(
      state,
      {
        entities: {[trackSchema.getKey()]: {[trackSchema.getId(track)]: {
          metadataLoadingState: {$set: MetaDataLoadingStates.idle}
        }}},
      }
    )
  },
  [METADATA_LOADING]: (state, action) => {
    const {track} = action.payload;
    return updateHelper(
      state,
      {entities: {[trackSchema.getKey()]: {[trackSchema.getId(track)]: {
        metadataLoadingState: {$set: MetaDataLoadingStates.loading}
      }}}}
    )
  },
  [METADATA_LOADED]: (state, action) => {
    const {track, metadata} = action.payload;
    return updateHelper(
      state,
      {
        entities: {[trackSchema.getKey()]: {[trackSchema.getId(track)]: {
          metadataLoadingState: {$set: MetaDataLoadingStates.loaded},
          metadata: {$set: metadata},
        }}},
      }
    )

  },
  [METADATA_LOAD_ERROR]: (state, action) => {
    const {track} = action.payload;
    return updateHelper(
      state,
      {
        entities: {[trackSchema.getKey()]: {[trackSchema.getId(track)]: {
          metadataLoadingState: {$set: MetaDataLoadingStates.error}
        }}},
      }
    )
  },
  [PLAYLIST_LIST_REQUESTED]: (state, action) => {
    return {
      ...state,
      playlistsLoadingState: LoadingStates.loading,
    }
  },
  [PLAYLIST_LIST_LOADED]: (state, action) => {
    const { playlists, filterby, sortby } = action.payload;
    const normalizedPlaylists = normalize(playlists, arrayOf(playlistSchema));
    return {
      ...state,
      playlists: normalizedPlaylists.result,
      entities: {
        ...state.entities,
        ...normalizedPlaylists.entities,
      },
      playlistsLoadingState: LoadingStates.loaded,
      playlistFilterBy: filterby,
      playlistSortBy: sortby,
    }
  },
  [PLAYLIST_LIST_LOAD_ERROR]: (state, action) => {
    return {
      ...state,
      playlistsLoadingState: LoadingStates.error,
    }
  },
  [PLAYLIST_LIST_SORT_BY]: (state, action) => {
    let sortReversed;
    // if the same sorting action is triggered again, reverse the sorting
    if (state.playlistSortBy == action.payload.sortBy) {
      sortReversed = !state.playlistSortByReversed;
    } else {
      // but when changing to another sort criteria, reset the reversing:
      sortReversed = false;
    }
    return {
      ...state,
      playlistSortBy: action.payload.sortBy,
      playlistSortByReversed:  sortReversed,
    }
  },
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
    const normTracks = normalize(
      tracks.map((track) => {
        track.metadataLoadingState = MetaDataLoadingStates.idle;
        return track;
      }),
      arrayOf(trackSchema)
    );
    const receivedEntities = {
      ...normCollection.entities,
      ...normTracks.entities,
    };
    const newEntities = {...state.entities};
    for (const model of Object.keys(receivedEntities)) {
      const receivedModelEntities = receivedEntities[model];
      const newModelEntities = newEntities[model];
      for (const modelKey of Object.keys(receivedModelEntities)){
        // do not overwrite any existing models:
        if (typeof newModelEntities[modelKey] === 'undefined'){
          newModelEntities[modelKey] = receivedModelEntities[modelKey];
        }
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

