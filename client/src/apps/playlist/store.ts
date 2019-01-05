import {Module} from "vuex";
import {FileInterface, TrackInterface, TrackType} from "@/api/types";
import {enumerate} from "@/common/utils";

type PlaylistType = {
    id: number,
    name: string,
    activeTrackIdx: number,
    tracks: TrackInterface[],
}

type PlaylistManagerState = {
    playlists: PlaylistType[],
    activePlaylistIdx: number,
    visiblePlaylistIdx: number,
}

const ADD_FILE_TO_PLAYLIST = 'ADD_FILE_TO_PLAYLIST';
const SWAP_TRACK = 'SWAP_TRACK';
const ADD_NEW_PLAYLIST = 'ADD_NEW_PLAYLIST';
const SET_ACTIVE_PLAYLIST_IDX = 'SET_ACTIVE_PLAYLIST_IDX';
const SET_VISIBLE_PLAYLIST_IDX = 'SET_VISIBLE_PLAYLIST_IDX';
const SET_ACTIVE_TRACK_IDX_IN_PLAYLIST = 'SET_ACTIVE_TRACK_IDX_IN_PLAYLIST';


const AudioPlayerStore: Module<PlaylistManagerState, any> = {
    namespaced: true,
    state () {
        return {
            activePlaylistIdx: 0,
            visiblePlaylistIdx: 0,
            playlists: [
                {
                    id: -1,
                    name: 'Lumpi',
                    activeTrackIdx: 0,
                    tracks: [
                        {
                            renderId: 1,
                            playlist: -1,
                            order: 0,
                            type: TrackType.File,
                            file: {
                                id: 0,
                                filename: '',
                                stream_url: '',
                                meta_data: {
                                    track: 1,
                                    track_total: 5,
                                    title: 'hello',
                                    artist: {
                                        name: 'artist',
                                        id: 1,
                                    },
                                    album: 'album',
                                    year: 2071,
                                    genre: 'rock',
                                    duration: 1238,
                                }
                            },
                            youtube_url: null,
                        },
                        {
                            renderId: 2,
                            playlist: -1,
                            order: 1,
                            type: TrackType.File,
                            file: {
                                id: 0,
                                filename: '',
                                stream_url: '',
                                meta_data: {
                                    track: 1,
                                    track_total: 5,
                                    title: 'hello2',
                                    artist: {
                                        name: 'artist2',
                                        id: 2,
                                    },
                                    album: 'album',
                                    year: 2071,
                                    genre: 'rock',
                                    duration: 238,
                                }
                            },
                            youtube_url: null,
                        },
                    ]
                },
            ]
        };
    },
    getters: {
        playlists: (state) => state.playlists,
        activePlaylistIdx: (state) => state.activePlaylistIdx,
        visiblePlaylistIdx: (state) => state.visiblePlaylistIdx,
        activePlaylist: (state) => state.playlists[state.activePlaylistIdx],
        activeTrack: (state, getters) => {
            const pl = getters.activePlaylist;
            return pl.tracks[pl.activeTrackIdx];
        }
    },
    actions: {
        addNewPlaylist: function ({commit, getters}) {
          commit(ADD_NEW_PLAYLIST);
          commit(SET_VISIBLE_PLAYLIST_IDX, getters.playlists.length - 1);
        },
        addFileToVisiblePlaylist: function ({commit, getters}, file) {
            const playlistIdx = getters.visiblePlaylistIdx;
            commit(ADD_FILE_TO_PLAYLIST, {playlistIdx, file});
        },
        swapTrackInActivePlaylist: function ({commit, getters}, {oldIndex, newIndex}) {
            const playlistIdx = getters.visiblePlaylistIdx;
            commit(SWAP_TRACK, {playlistIdx, oldIndex, newIndex});
        },
        setActivePlaylistIdx: function ({commit}, playlistIdx) {
            commit(SET_ACTIVE_PLAYLIST_IDX, playlistIdx);
        },
        setVisiblePlaylistIdx: function ({commit}, playlistIdx) {
            commit(SET_VISIBLE_PLAYLIST_IDX, playlistIdx);
        },
        play: function ({commit, getters, dispatch}, {playlistIdx, trackIdx}) {
            commit(SET_ACTIVE_PLAYLIST_IDX, playlistIdx);
            commit(SET_ACTIVE_TRACK_IDX_IN_PLAYLIST, {playlistIdx, trackIdx});
            const track = getters.activeTrack;
            dispatch('audioplayer/play', {track}, {root: true});
        }
    },
    mutations: {
        [ADD_FILE_TO_PLAYLIST]: (state, {playlistIdx, file}) => {
            state.playlists[playlistIdx].tracks.push({
                renderId: (Math.random() * 10000000) | 0,
                playlist: -1,
                order: state.playlists[playlistIdx].tracks.length,
                type: TrackType.File,
                file: file,
                youtube_url: null,
            });
        },
        [SWAP_TRACK]: (state, {playlistIdx, oldIndex, newIndex}) => {
            const tracks = state.playlists[playlistIdx].tracks;
            const swappedTrack = tracks[oldIndex];
            // remove the track from it's old position
            let newTracks = [...tracks.slice(0, oldIndex), ...tracks.slice(oldIndex + 1)];
            newTracks.splice(newIndex, 0, swappedTrack);
            for (const [idx, track] of enumerate(newTracks)) {
                track.order = idx;
            }
            state.playlists[playlistIdx].tracks = newTracks;
        },
        [ADD_NEW_PLAYLIST]: (state) => {
            state.playlists = [
                ...state.playlists,
                {
                    id: -(Math.random() * 1000000 | 0),
                    name: 'New Playlist',
                    activeTrackIdx: 0,
                    tracks: []
                }
            ]
        },
        [SET_ACTIVE_PLAYLIST_IDX]: (state, playlistIdx) => {
            state.activePlaylistIdx = playlistIdx;
        },
        [SET_VISIBLE_PLAYLIST_IDX]: (state, playlistIdx) => {
            state.visiblePlaylistIdx = playlistIdx;
        },
        [SET_ACTIVE_TRACK_IDX_IN_PLAYLIST]: (state, {playlistIdx, trackIdx}) => {
            state.playlists[playlistIdx].activeTrackIdx = trackIdx;
        },
    },
};

export default AudioPlayerStore;
