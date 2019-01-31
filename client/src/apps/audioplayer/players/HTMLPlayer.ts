import {TrackType} from "@/api/types";
import * as _ from "lodash";
import {PlayerEventType} from "@/apps/audioplayer/store";
import {AbstractAudioPlayer} from "@/apps/audioplayer/players/AbstractAudioPlayer";
import {OfflineStorage} from "@/apps/offline/storage";
import {Settings} from "@/api/api";


export class HTMLPlayer extends AbstractAudioPlayer {
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

    async _playCurrentTrack (): Promise<any> {
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

        const offlineStorage = OfflineStorage.getInstance();
        const offlineTrack = await offlineStorage.get(this._currentTrack);
        if (offlineTrack) {
            this.htmlAudioTag.src = URL.createObjectURL(offlineTrack);
        } else {
            this.htmlAudioTag.src = this._currentTrack.file.stream_url + '?authtoken=' + Settings.getAuthToken();
        }
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
