import { takeEvery, takeLatest } from 'redux-saga'
import { call, put, select } from 'redux-saga/effects'

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
  const {sortby, filterby} = action.payload;
  try {
    const state = yield select();
    const getState = () => state;
    const playlists = yield fetchPlaylistList(getState, sortby, filterby);
    yield put(actionPlaylistListLoaded(playlists, sortby, filterby));
  } catch (error) {
    yield put(actionPlaylistListLoadError());
  }
}

export function* onPlaylistOpenRequested (action) {
  const state = yield select();
  const getState = () => state;
  const {playlistId} = action.payload;
  yield put(actionPlaylistDetailLoading(playlistId));
  yield put(actionOpenPlaylistTab(playlistId));
  yield put(actionActivatePlaylist(playlistId));
  try {
    const playlistData = yield fetchPlaylistDetail(getState, playlistId);
    yield put(actionPlaylistDetailLoaded(playlistId, playlistData));
  } catch (error) {
    console.log(error);
    yield put(actionClosePlaylistTab(playlistId));
    yield put(actionErrorMessage("Error loading playlist"));
  }
}

export function* onInit (action) {
  yield
}

export function* onPlaylistCreateRequested (action) {
  const state = yield select();
  const newPlaylistId = -Math.floor(Math.random() * 1000000);
  yield put(actionPlaylistCreate(newPlaylistId));
  yield put(actionOpenPlaylistTab(newPlaylistId));
}


export function* PlaylistLoaderSaga () {
  // init
  yield fork(actionPlaylistCreateRequested());
  yield [
    takeLatest(PLAYLIST_LIST_REQUESTED, onPlaylistListRequested),
    takeLatest(PLAYLIST_OPEN_REQUESTED, onPlaylistOpenRequested),
    takeLatest(CREATE_PLAYLIST_REQUESTED, onPlaylistCreateRequested)
  ];
}

