import {Module} from "vuex";


type TrackType = {
    title: string,
}

type PlaylistType = {
    id: number,
    name: string,
    activeTrack: number,
    tracks: TrackType[],
}

type PlaylistManagerState = {
    playlists: PlaylistType[],
    activePlaylistIdx: number,
}

import * as _ from 'lodash';

const AudioPlayerStore: Module<PlaylistManagerState, any> = {
    namespaced: true,
    state () {
        return {
            activePlaylistIdx: 0,
            playlists: [{
                id: 123,
                name: 'Lumpi',
                activeTrack: 0,
                tracks: [
                    {'title': 'asd'},
                    {'title': 'asd2qe23ra'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                    {'title': 'agsar436 g>gsd'},
                ]
            },
                {
                    id: 1234,
                    name: 'SCHUallls',
                    activeTrack: 2,
                    tracks: [
                        {'title': 'asd424w3r'},
                        {'title': 'asd2qe23ra'},
                        {'title': 'agsar436 sfdg>gsd'},
                    ]
                }
            ]
        };
    },
    getters: {
        playlists: (state) => state.playlists,
        activePlaylistIdx: (state) => state.activePlaylistIdx,
    },
    actions: {

    },
    mutations: {

    },
};

export default AudioPlayerStore;
