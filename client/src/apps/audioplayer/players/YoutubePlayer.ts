import {TrackType} from "@/api/types";
import {injectCSS} from "@/common/html";
import {PlayerEventType} from "@/apps/audioplayer/store";
import {AbstractAudioPlayer} from "@/apps/audioplayer/players/AbstractAudioPlayer";
//@ts-ignore
import YouTubePlayerWrapper from 'youtube-player';


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


export class YoutubePlayer extends AbstractAudioPlayer {

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

    async _playCurrentTrack (): Promise<any> {
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
