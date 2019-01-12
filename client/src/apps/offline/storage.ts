//@ts-ignore
import idbKvStore from 'idb-kv-store';
import {TrackInterface, TrackType} from "@/api/types";

interface idbKvStoreInstance {
    set: (key: string, value: any) => Promise<any>;
    get: (key: string) => Promise<any>;
    add: (key: string, value: any) => Promise<any>;
    getMultiple: (keys: string[]) => Promise<any>;
    remove: (key: string) => Promise<any>;
    keys: (range?: IDBKeyRange) => Promise<any>;
}

const keyForTrack = (track: TrackInterface): string => {
    switch (track.type) {
        // @ts-ignore
        case TrackType.File: return track.file.id;
        // @ts-ignore
        case TrackType.Youtube: return `youtube-${track.youtube.video_id}`;
        default: throw new Error('Cannot generate key for track type ' + track.type);
    }
};


export class OfflineStorage {
    private static _instance: OfflineStorage | null = null;

    private kvStore: idbKvStoreInstance;

    private constructor () {
        this.kvStore = idbKvStore('offline-file-storage');
    }

    public static getInstance (): OfflineStorage {
        if (OfflineStorage._instance === null) {
            OfflineStorage._instance = new OfflineStorage();
        }
        return OfflineStorage._instance;
    }

    getOfflineTrackIds () {
        return this.kvStore.keys();
    }

    set(track: TrackInterface, value: any) {
        this.kvStore.set(keyForTrack(track), value);
    }

    get(track: TrackInterface) {
        return this.kvStore.get(keyForTrack(track));
    }
}
