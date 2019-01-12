import {TrackInterface, TrackType} from "@/api/types";
import {PlayerEvent, PlayerEventType} from "@/apps/audioplayer/store";

export abstract class AbstractAudioPlayer {
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

    abstract async _playCurrentTrack (): Promise<any>;
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
