import {Module} from "vuex";
import {AbstractAudioPlayer} from "@/apps/audioplayer/players/AbstractAudioPlayer";
import {HTMLPlayer} from "@/apps/audioplayer/players/HTMLPlayer";
import {YoutubePlayer} from "@/apps/audioplayer/players/YoutubePlayer";

const SET_ACTIVE_PLAYER = 'SET_ACTIVE_PLAYER';
const SET_PLAYTIME = 'SET_PLAYTIME';
const SET_DURATION = 'SET_DURATION';
const SET_META_DATA_DURATION = 'SET_META_DATA_DURATION';
const ADD_PLAYER_STATE_LISTENER = 'ADD_PLAYER_STATE_LISTENER';
const ADD_AUDIO_PLAYER = 'ADD_AUDIO_PLAYER';

export enum PlayerEventType {
    Ended,
    TimeUpdate,
    MetaDuration,
    UnrecoverablePlaybackError,
}

interface PlayerEventPayloadTimeUpdate {
    currentTime: number,
    duration: number,
}

interface PlayerEventPayloadMetaDuration {
    duration: number | null,
}

export interface PlayerEvent {
    type: PlayerEventType,
    payload?: PlayerEventPayloadTimeUpdate | PlayerEventPayloadMetaDuration,
}


type AudioPlayerState = {
    src: string | null,
    currentPlaytime: number,
    duration: number,
    metaDataDuration: null | number,
    playerStateListeners: Function[],
    activePlayer: AbstractAudioPlayer | null,
    audioPlayers: AbstractAudioPlayer[],
}


const AudioPlayerStore: Module<AudioPlayerState, any> = {
    namespaced: true,
    state () {
        return {
            src: null,
            currentPlaytime: 0,
            duration: 1,
            metaDataDuration: null,
            playerStateListeners: [],
            audioPlayers: [],
            activePlayer: null,
        };
    },
    getters: {
        currentPlaytime: (state) => state.currentPlaytime,
        duration: (state) => state.duration,
        src: (state) => state.src,
    },
    actions: {
        init ({commit, state, dispatch}) {
            dispatch('addAudioPlayer', new HTMLPlayer());
            dispatch('addAudioPlayer', new YoutubePlayer());
        },
        addAudioPlayer ({commit, state}, audioPlayer: AbstractAudioPlayer) {
            commit(ADD_AUDIO_PLAYER, audioPlayer);
            audioPlayer.addPlayerEventListener((event: PlayerEvent) => {
                if (event.type === PlayerEventType.TimeUpdate) {
                    const payload = (event.payload as PlayerEventPayloadTimeUpdate);
                    if (!payload) throw new Error('event payload is null');
                    commit(SET_DURATION, payload.duration);
                    commit(SET_PLAYTIME, payload.currentTime);
                }
                for (const listener of state.playerStateListeners) {
                    listener(event);
                }
            })
        },
        addPlayerListener ({commit}, listener) {
            commit(ADD_PLAYER_STATE_LISTENER, listener);
        },
        play ({commit, state, dispatch}, {track}) {
            // stop all players
            for (const player of state.audioPlayers) {
                player.stop();
            }
            for (const player of state.audioPlayers) {
                if (player.canPlayTrack(track)) {
                    commit(SET_ACTIVE_PLAYER, player);
                    player.play(track);
                    return;
                }
            }
            alert(`Don't know how to play track type ${track.type}`);
        },
        resume ({state}) {
            if (state.activePlayer === null) {
                console.error('activePlayer is null, cannot resume');
                return;
            }
            state.activePlayer.resume();
        },
        pause ({state}) {
            if (state.activePlayer === null) {
                console.error('activePlayer is null, cannot pause');
                return;
            }
            state.activePlayer.pause();
        },
        jumpToPercentage ({state, getters}, percentage) {
            if (state.activePlayer === null) {
                throw new Error('Audioplayer not initialized, cannot jump.');
            }
            state.activePlayer.seekToPercentage(percentage);
        }
    },
    mutations: {
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
        [SET_ACTIVE_PLAYER] (state, activePlayer) {
            state.activePlayer = activePlayer;
        },
        [ADD_AUDIO_PLAYER] (state, audioPlayer) {
            state.audioPlayers.push(audioPlayer);
        }
    },
};

export default AudioPlayerStore;
