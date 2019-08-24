import {Module} from "vuex";
import {OfflineStorage} from "@/apps/offline/storage";
import {TrackInterface} from "@/api/types";

export type OfflineStoreState = {
    offlineTrackIds: number[],
}

const SET_OFFLINE_TRACK_IDS = 'SET_OFFLINE_TRACK_IDS';
const ADD_OFFLINE_TRACK_ID = 'ADD_OFFLINE_TRACK_ID';
const CLEAR = 'CLEAR';


const OfflineStore: Module<OfflineStoreState, any> = {
    namespaced: true,
    state () {
        return {
            offlineTrackIds: [],
        };
    },
    getters: {
        offlineTrackIds: (state) => state.offlineTrackIds,
    },
    actions: {
        init: async function ({commit}) {
            const storage = OfflineStorage.getInstance();
            commit(SET_OFFLINE_TRACK_IDS, await storage.getOfflineTrackIds());
        },
        makeAvailableOffline: async function ({dispatch}, track: TrackInterface) {
            if (track.file === null) {
                throw new Error('Cannot make track available offline, it does not have a `file`')
            }
            const response: Response = await fetch(track.file.stream_url);
            const data = await response.blob();
            dispatch('addToOfflineTracks', {track: track, data: data});
        },
        addToOfflineTracks: function ({commit}, {track, data}) {
            const storage = OfflineStorage.getInstance();
            storage.set(track, data);
            commit(ADD_OFFLINE_TRACK_ID, track.file.id);
        },
        clearStorage: function ({commit}) {
            const storage = OfflineStorage.getInstance();
            storage.clear();
            commit(CLEAR);
        }
    },
    mutations: {
        [SET_OFFLINE_TRACK_IDS]: (state, offlineTrackIds: number[]) => {
            state.offlineTrackIds = offlineTrackIds;
        },
        [ADD_OFFLINE_TRACK_ID]: (state, trackId) => {
            state.offlineTrackIds.push(trackId);
        },
        [CLEAR]: (state) => {
            state.offlineTrackIds = [];
        }

    },
};

export default OfflineStore;
