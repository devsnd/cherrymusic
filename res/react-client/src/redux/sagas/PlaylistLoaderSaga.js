import { takeEvery, takeLatest } from 'redux-saga'
import { call, put, select } from 'redux-saga/effects'

import {
  PLAYLIST_LIST_REQUESTED,
  PLAYLIST_OPEN_REQUESTED,
  fetchPlaylistList,
  actionPlaylistListLoaded,
  actionPlaylistListLoadError,
} from 'redux/modules/CherryMusicApi';

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
  //yield put(actionPlaylistDetailLoading, playlist);
  //playlist = yield fetchPlaylistDetail(getState, action.payload.playlistId);
  //yield put(actionPlaylistDetailLoaded, playlist);
  //yield put(actionOpenPlaylist)
}


export function* PlaylistLoaderSaga () {
  yield [
    takeLatest(PLAYLIST_LIST_REQUESTED, onPlaylistListRequested),
    takeLatest(PLAYLIST_OPEN_REQUESTED, onPlaylistOpenRequested),
  ];
}

