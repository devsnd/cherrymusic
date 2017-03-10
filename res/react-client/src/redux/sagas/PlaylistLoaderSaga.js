import {
  actionHammer,
  actionPlaylistListRequested,
  PlaylistSortModes
} from 'redux/modules/CherryMusicApi';
import { takeEvery, takeLatest } from 'redux-saga';
import { call, put, select, fork } from 'redux-saga/effects';

import {
  // playlist list
  PLAYLIST_LIST_REQUESTED,
  PLAYLIST_OPEN_REQUESTED,
  fetchPlaylistList,
  actionPlaylistListLoaded,
  actionPlaylistListLoadError,

  // playlist detail
  fetchPlaylistDetail,
  actionPlaylistOpenRequested,
  actionPlaylistDetailLoading,
  actionPlaylistDetailLoaded,
  actionPlaylistDetailLoadError,

  // playlist creation and saving
  actionPlaylistCreate,

  // playlist deletion
  PLAYLIST_DELETE_REQUESTED,
  actionPlaylistDeleted,
  deletePlaylist,

  // playlist modification
  playlistSetPublic,
  PLAYLIST_SET_PUBLIC_REQUESTED,
} from 'redux/modules/CherryMusicApi';

import {
  CREATE_PLAYLIST_REQUESTED,
  actionCreatePlaylistRequested,
  actionOpenPlaylistTab,
  actionActivatePlaylist,
  actionClosePlaylistTab,
} from 'redux/modules/PlaylistManager';

import {
  actionErrorMessage,
} from 'redux/modules/Messages';

export function* onPlaylistListRequested (action) {
  const {sortby, filterby } = action.payload;
  try {
    const state = yield select();
    const getState = () => state;
    const playlists = yield fetchPlaylistList(getState, sortby, filterby);
    yield put(actionPlaylistListLoaded(playlists, sortby, filterby));
  } catch (error) {
    console.log(error);
    yield put(actionPlaylistListLoadError());
    throw error;
  }
}

export function* onPlaylistOpenRequested (action) {
  const state = yield select();
  const getState = () => state;
  const {playlistId } = action.payload;
  yield put(actionPlaylistDetailLoading(playlistId));
  yield put(actionOpenPlaylistTab(playlistId));
  yield put(actionActivatePlaylist(playlistId));
  try {
    const playlistData = yield fetchPlaylistDetail(getState, playlistId);
    yield put(actionPlaylistDetailLoaded(playlistId, playlistData));
  } catch (error) {
    console.log(error);
    yield put(actionClosePlaylistTab(playlistId));
    yield put(actionErrorMessage('Error loading playlist'));
  }
}

export function* onPlaylistCreateRequested (action) {
  const state = yield select();
  const newPlaylistId = -Math.floor(Math.random() * 1000000);
  yield put(actionPlaylistCreate(newPlaylistId));
  yield put(actionOpenPlaylistTab(newPlaylistId));
  yield put(actionActivatePlaylist(newPlaylistId));
}

function* onPlaylistDeleteRequested (action) {
  const {playlistId} = action.payload;
  const state = yield select();
  const getState = () => state;
  try {
    yield deletePlaylist(getState, playlistId);
    yield put(actionPlaylistDeleted(playlistId));
  } catch (error) {
    console.error(error);
  }
}

function* onPlaylistSetPublicRequested (action) {
  const {playlistId, isPublic} = action.payload;
  const state = yield select();
  const getState = () => state;
  try {
    yield playlistSetPublic(getState, playlistId, isPublic);
  } catch (error) {
    console.error(error);
    return
  }
  yield put(actionHammer(
    {entities: {playlist: {[playlistId]: {'public': {$set: isPublic}}}}}
  ));
}

export function* PlaylistLoaderSaga () {
  yield [
    takeLatest(CREATE_PLAYLIST_REQUESTED, onPlaylistCreateRequested),
    takeLatest(PLAYLIST_LIST_REQUESTED, onPlaylistListRequested),
    takeLatest(PLAYLIST_OPEN_REQUESTED, onPlaylistOpenRequested),
    takeLatest(PLAYLIST_DELETE_REQUESTED, onPlaylistDeleteRequested),
    takeLatest(PLAYLIST_SET_PUBLIC_REQUESTED, onPlaylistSetPublicRequested),
    // init
    takeLatest('redux/cherrymusic/LOG_IN_SUCCESS', function* () {
      yield put(actionCreatePlaylistRequested());
    }),
  ];
}

