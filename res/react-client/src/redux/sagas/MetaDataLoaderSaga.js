import { takeEvery, takeLatest } from 'redux-saga'
import { call, put, select } from 'redux-saga/effects'

import {
  DIRECTORY_LOADED,
  PLAYLIST_DETAIL_LOADED,
  fetchTrackMetaData,
  selectEntitiesTrackByNewTrack,
  actionMetaDataLoaded,
  actionMetaDataLoading,
  actionMetaDataLoadError,
  MetaDataLoadingStates,
  selectTrackMetaDataLoadingState,
} from 'redux/modules/CherryMusicApi';


import {
  METADATA_LOADED,
  METADATA_LOAD_ERROR,
  METADATA_LOAD_ENQUEUE,
} from 'redux/modules/CherryMusicApi';

function* onTracksLoaded (action) {
  const {tracks} = action.payload;
  const trackSelector = yield select(selectEntitiesTrackByNewTrack);
  for (const track of tracks) {
    const loadedTrack = trackSelector(track);
    if (
      !loadedTrack
      ||
      // do not load meta data of any track twice
      selectTrackMetaDataLoadingState(loadedTrack) === MetaDataLoadingStates.idle
    ) {
      try {
        yield put(actionMetaDataLoading(track, metadata));
        const metadata = JSON.parse(yield call(fetchTrackMetaData, track));
        yield put(actionMetaDataLoaded(track, metadata));
      } catch (error) {
        yield put(actionMetaDataLoadError(track));
      }
    }
  }
}

export function* MetaDataWatcher() {
  yield* takeLatest([DIRECTORY_LOADED, PLAYLIST_DETAIL_LOADED], onTracksLoaded);
}
