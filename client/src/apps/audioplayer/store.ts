import {Module} from "vuex";

const SET_AUDIO_TAG = 'SET_AUDIO_TAG';
const SET_PLAYTIME = 'SET_PLAYTIME';
const SET_DURATION = 'SET_DURATION';


type AudioPlayerState = {
    src: string | null,
    currentPlaytime: number,
    duration: number,
    metaDataDuration: null | number,
    audioTag: HTMLMediaElement | null,
}

import * as _ from 'lodash';

const AudioPlayerStore: Module<AudioPlayerState, any> = {
    namespaced: true,
    state () {
        return {
            src: null,
            currentPlaytime: 0,
            duration: 1,
            metaDataDuration: null,
            audioTag: null,
        };
    },
    getters: {
        currentPlaytime: (state) => state.currentPlaytime,
        duration: (state) => state.metaDataDuration || state.duration,
        src: (state) => state.src,
    },
    actions: {
        async registerAudioTag ({commit, state}, audioTag) {
            const setCurrentPlaytime = () => {
                console.log('debounce');
                commit(SET_PLAYTIME, audioTag.currentTime)
                commit(SET_DURATION, audioTag.duration);
            };
            audioTag.ontimeupdate = _.throttle(
                setCurrentPlaytime,
                1000,
                {trailing: true}
            );
            commit(SET_AUDIO_TAG, audioTag);
        },
        playFile ({commit, state}, filePath) {
            console.log('playing ', filePath);
            if (state.audioTag === null) {
                console.error('Cannot play file, audioTag not set!');
                return;
            }
            state.audioTag.src = filePath;
            state.audioTag.play();
        }
    },
    mutations: {
        [SET_AUDIO_TAG] (state, audioTag) {
            state.audioTag = audioTag;
        },
        [SET_PLAYTIME] (state, playtime) {
            state.currentPlaytime = playtime;
        },
        [SET_DURATION] (state, duration) {
            state.duration = duration;
        }
    },
};

export default AudioPlayerStore;
