import {Module} from "vuex";
import * as _ from 'lodash';
import {FileInterface, TrackInterface, TrackType, YoutubeInterface} from "@/api/types";
//@ts-ignore
import YouTubePlayerWrapper from 'youtube-player';
import {injectCSS} from "@/common/html";

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
    activePlayer: AudioPlayer | null,
    audioPlayers: AudioPlayer[],
}


enum YoutubeStateChangeData {
    unstarted = -1,
    ended = 0,
    playing = 1,
    paused = 2,
    buffering = 3,
    video_cued = 5,
}

type YoutubeStateChangeEvent = {
    data: YoutubeStateChangeData,
    target: any,
}

enum YoutubeErrorType {
    invalidId = 2,
    cannotPlayInHTML5 = 5,
    videoNotFound = 100,
    videoNotEmbeddable = 101,
    videoNotEmbeddable2 = 150,
}

type YoutubeErrorEvent = {
    target: any,
    data: YoutubeErrorType,
}


abstract class AudioPlayer {
    _currentTrack: TrackInterface | null;
    _supportedTrackTypes: TrackType[] = [];
    _playerEventListener: Function[];
    _currentTime: number = 0;
    _duration: number = 0;
    _metaDuration: number | null = null;

    play (track: TrackInterface): void {
        if (this._supportedTrackTypes.indexOf(track.type) === -1) {
            throw new Error(`${this} cannot play track of type ${track.type}`)
        }
        this._currentTrack = track;
        // reset the meta duration of the track. It should be set by
        // `_callCurrentTrack`.
        this.setMetaDuration(null);
        this._playCurrentTrack();
    }

    abstract _playCurrentTrack (): void;
    abstract stop  (): void;
    abstract pause  (): void;
    abstract resume  (): void;
    abstract seekTo (seconds: number): void;

    canPlayTrack (track: TrackInterface) {
        return this._supportedTrackTypes.indexOf(track.type) !== -1;
    }

    seekToPercentage (percentage: number) {
        const duration = this._metaDuration || this._duration;
        this.seekTo(duration * percentage);
    }

    setMetaDuration (duration: number | null) {
        // sometimes we only know the length of the stream from meta-data
        // and not while actually streaming the track. This can be called
        // to override the "duration" set by `setTimeAndDuration`.
        // Call this in the beginning of `_playCurrentTrack`.
        this.emitEvent(
            {type: PlayerEventType.MetaDuration, payload: {duration: duration}}
        );
    }

    setTimeAndDuration (currentTime: number, duration: number): void {
        this._currentTime = currentTime;
        this._duration = duration;
        this.emitEvent({
            type: PlayerEventType.TimeUpdate,
            payload: {
                currentTime: currentTime,
                duration: duration,
            }
        });
    };

    constructor (supportedTrackTypes: TrackType[]) {
        this._playerEventListener = [];
        this._currentTrack = null;
        this._supportedTrackTypes = supportedTrackTypes;
    }

    addPlayerEventListener (listener: Function) {
        this._playerEventListener.push(listener);
    }

    emitEvent (event: PlayerEvent) {
        for (const listener of this._playerEventListener) {
            listener(event);
        }
    }
}


class YoutubePlayer extends AudioPlayer {

    _youtubePlayer: any;

    constructor () {
        super([TrackType.Youtube]);

        const youtubeContainer = document.createElement('div');
        youtubeContainer.id = 'youtube-container';
        document.body.appendChild(youtubeContainer);
        injectCSS('#youtube-container { display: none; }');

        this._youtubePlayer = YouTubePlayerWrapper('youtube-container');
        this._youtubePlayer.on('stateChange', (event: YoutubeStateChangeEvent) => {
            if (event.data === YoutubeStateChangeData.ended) {
                this.emitEvent({type: PlayerEventType.Ended});
            }
        });
        this._youtubePlayer.on('error', (event: YoutubeErrorEvent) => {
            this.emitEvent({type: PlayerEventType.UnrecoverablePlaybackError});
        });
        // check regularly if the youtube video is progressing
        let lastCurrentTime: number = -1;
        window.setInterval(
            async () => {
                const currentTime = await this._youtubePlayer.getCurrentTime();
                const duration = await this._youtubePlayer.getDuration();
                if (lastCurrentTime !== currentTime) {
                    // the player did something, lets tell the others.
                    lastCurrentTime = currentTime;
                    this.setTimeAndDuration(currentTime, duration);

                }
            }, 1000
        );
    }

    pause (): void {
        this._youtubePlayer.pauseVideo();
    }

    resume (): void {
        this._youtubePlayer.playVideo();
    }

    stop (): void {
        this._youtubePlayer.stopVideo();
    }

    _playCurrentTrack (): void {
        if (this._currentTrack === null) {
            throw new Error('_currenTrack is null');
        }
        if (this._currentTrack.youtube === null) {
            throw new Error('youtube is null');
        }
        this._youtubePlayer.loadVideoById(this._currentTrack.youtube.youtube_id, 0.1);
        this._youtubePlayer.playVideo();
    }

    seekTo(seconds: number): void {
        this._youtubePlayer.seekTo(seconds);
    }
}

class HTMLPlayer extends AudioPlayer {
    private htmlAudioTag: HTMLMediaElement;

    constructor () {
        super([TrackType.File]);

        this.htmlAudioTag = document.createElement('audio');
        this.htmlAudioTag.id = 'html-audio-player';
        document.body.appendChild(this.htmlAudioTag);

        const setCurrentPlaytime = () => this.setTimeAndDuration(
            this.htmlAudioTag.currentTime,
            this.htmlAudioTag.duration
        );
        this.htmlAudioTag.ontimeupdate = _.throttle(
            setCurrentPlaytime,
            1000,
            {trailing: true}
        );
        this.htmlAudioTag.onended = () => {
            this.emitEvent({type: PlayerEventType.Ended});
        };
    }

    _playCurrentTrack (): void {
        if (this._currentTrack === null) {
            throw new Error('_currentTrack is null')
        }
        if (this._currentTrack.file === null) {
            throw new Error('_currentTrack.file is null!');
        }
        const file = this._currentTrack.file;
        const metaDuration = (
            file.meta_data && file.meta_data.duration || null
        );
        if (metaDuration) {
            this.setMetaDuration(metaDuration)
        }

        this.htmlAudioTag.src = this._currentTrack.file.stream_url;
        this.htmlAudioTag.play();
    }

    pause (): void {
        this.htmlAudioTag.pause();
    }

    resume (): void {
        this.htmlAudioTag.play();
    }

    seekTo(seconds: number): void {
        this.htmlAudioTag.currentTime = seconds;
    }

    stop (): void {
        this.htmlAudioTag.pause();
        this.htmlAudioTag.currentTime = 0;
    }

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
        addAudioPlayer ({commit, state}, audioPlayer: AudioPlayer) {
            commit(ADD_AUDIO_PLAYER, audioPlayer);
            audioPlayer.addPlayerEventListener((event: PlayerEvent) => {
                if (event.type === PlayerEventType.TimeUpdate) {
                    if (!event.payload) throw new Error('event payload is null');
                    commit(SET_DURATION, event.payload.duration);
                    //TODO why?
                    commit(SET_PLAYTIME, (event.payload as any).currentTime);
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
