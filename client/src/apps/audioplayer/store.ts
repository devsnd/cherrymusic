import {Module} from "vuex";
import * as _ from 'lodash';
import {FileInterface, TrackInterface, TrackType, YoutubeInterface} from "@/api/types";

const SET_AUDIO_TAG = 'SET_AUDIO_TAG';
const SET_PLAYTIME = 'SET_PLAYTIME';
const SET_DURATION = 'SET_DURATION';
const SET_META_DATA_DURATION = 'SET_META_DATA_DURATION';
const ADD_PLAYER_STATE_LISTENER = 'ADD_PLAYER_STATE_LISTENER';
const SET_YOUTUBE_PLAYER = 'SET_YOUTUBE_PLAYER';

export enum PlayerEventType {
    Ended,
    TimeUpdate,
}

export type PlayerEvent = {
    type: PlayerEventType,
    payload?: any,
}


type AudioPlayerState = {
    src: string | null,
    currentPlaytime: number,
    duration: number,
    metaDataDuration: null | number,
    audioTag: HTMLMediaElement | null,
    playerStateListeners: Function[],
    youtubePlayer: null | any,
}


enum YoutubeStateChangeData {
    unstarted = -1,
    ended = 0,
    playing = 1,
    paused = 2,
    buffering = 3,
    video_cued = 5,
}

type YoutubeStateChange = {
    data: YoutubeStateChangeData,
    target: any,
}


//@ts-ignore
import YouTubePlayer from 'youtube-player';

const AudioPlayerStore: Module<AudioPlayerState, any> = {
    namespaced: true,
    state () {
        return {
            src: null,
            currentPlaytime: 0,
            duration: 1,
            metaDataDuration: null,
            audioTag: null,
            playerStateListeners: [],
            youtubePlayer: null,
        };
    },
    getters: {
        currentPlaytime: (state) => state.currentPlaytime,
        duration: (state) => state.duration,
        src: (state) => state.src,
    },
    actions: {
        setCurrentPlaytime ({commit, dispatch}, {currentTime, duration}) {
            commit(SET_PLAYTIME, currentTime);
            if (duration !== null) {
                commit(SET_DURATION, duration);
            }
            dispatch(
                'emitEvent',
                {
                    type: PlayerEventType.TimeUpdate,
                    payload: {currentTime: currentTime}
                }
            )
        },
        async registerAudioTag ({commit, state, dispatch}, audioTag) {
            const setCurrentPlaytime = () => (
                dispatch(
                    'setCurrentPlaytime',
                    {currentTime: audioTag.currentTime, duration: audioTag.duration}
                )
            );
            audioTag.ontimeupdate = _.throttle(
                setCurrentPlaytime,
                1000,
                {trailing: true}
            );
            audioTag.onended = () => {
                dispatch('emitEvent', {type: PlayerEventType.Ended});
            };
            commit(SET_AUDIO_TAG, audioTag);
        },
        initYoutubePlayer ({commit, dispatch}) {
            const youtubeContainer = document.createElement('div');
            youtubeContainer.id = 'youtube-container';
            document.body.appendChild(youtubeContainer);
            const youtubePlayer = YouTubePlayer('youtube-container');
            youtubePlayer.on('stateChange', (event: YoutubeStateChange) => {
                if (event.data === YoutubeStateChangeData.ended) {
                    dispatch('emitEvent', {type: PlayerEventType.Ended});
                }
            });
            // check regularly if the youtube video is progressing
            let lastCurrentTime: number = -1;
            window.setInterval(
                async () => {
                    const currentTime = await youtubePlayer.getCurrentTime();
                    if (lastCurrentTime !== currentTime) {
                        // the player did something, lets tell the others.
                        lastCurrentTime = currentTime;
                        const duration = await youtubePlayer.getDuration();
                        dispatch('setCurrentPlaytime', {currentTime, duration})
                    }
                }, 1000
            );

            commit(SET_YOUTUBE_PLAYER, youtubePlayer);
        },
        emitEvent ({state}, event: PlayerEvent) {
            for (const listener of state.playerStateListeners) {
                listener(event);
            }
        },
        addPlayerListener ({commit}, listener) {
            commit(ADD_PLAYER_STATE_LISTENER, listener);
        },
        play ({commit, state, dispatch}, {track}) {
            if (track.type === TrackType.File) {
                dispatch('playFile', track.file);
            } else if (track.type === TrackType.Youtube) {
                dispatch('playYoutube', track.youtube);
            } else {
                alert(`Don't know how to play track type ${track.type}`)
            }
        },
        playFile ({commit, state}, file: FileInterface) {
            const metaDataDuration = (
                file.meta_data && file.meta_data.duration || null
            );
            commit(SET_META_DATA_DURATION, metaDataDuration);

            if (state.audioTag === null) {
                console.error('Cannot play file, audioTag not set!');
                return;
            }
            state.audioTag.src = file.stream_url;
            state.audioTag.play();
        },
        playYoutube ({commit, state}, youtube: YoutubeInterface) {
            if (state.youtubePlayer === null) {
                alert('Cannot play youtube video, youtube player not initialized');
                return;
            }
            state.youtubePlayer.loadVideoById(youtube.youtube_id);
            state.youtubePlayer.playVideo();
        },
        jumpToPercentage ({state, getters}, percentage) {
            if (state.audioTag === null) {
                throw new Error('Audioplayer not initialized, cannot jump.');
            }
            state.audioTag.currentTime = getters.duration * percentage;
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
        },
        [SET_META_DATA_DURATION] (state, duration) {
            state.metaDataDuration = duration;
        },
        [ADD_PLAYER_STATE_LISTENER] (state, listener) {
            state.playerStateListeners.push(listener);
        },
        [SET_YOUTUBE_PLAYER] (state, youtubePlayer) {
            state.youtubePlayer = youtubePlayer;
        }
    },
};

export default AudioPlayerStore;
