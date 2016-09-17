import { takeEvery, takeLatest } from 'redux-saga'
import { call, put, select } from 'redux-saga/effects'

import {
  PLAYLIST_LIST_REQUESTED,
  PLAYLIST_OPEN_REQUESTED,
  fetchPlaylistList,
  actionPlaylistListLoaded,
  actionPlaylistListLoadError,

  fetchPlaylistDetail,
  actionPlaylistOpenRequested,
  actionPlaylistDetailLoading,
  actionPlaylistDetailLoaded,
  actionPlaylistDetailLoadError,
  actionOpenLoadingPlaylist,
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
  const {playlistId} = action.payload;
  yield put(actionPlaylistDetailLoading(playlistId));
  yield put(actionOpenLoadingPlaylist(playlistId));
  try {
    playlist = yield fetchPlaylistDetail(getState, playlistId);
    yield put(playlistId, actionPlaylistDetailLoaded(playlist));
  } catch (error) {
    yield put(actionPlaylistDetailLoadError(playlistId));
  }
}


export function* PlaylistLoaderSaga () {
  yield [
    takeLatest(PLAYLIST_LIST_REQUESTED, onPlaylistListRequested),
    takeLatest(PLAYLIST_OPEN_REQUESTED, onPlaylistOpenRequested),
  ];
}

