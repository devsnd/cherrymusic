import {Module} from "vuex";
import {FileInterface, TrackInterface, TrackType} from "@/api/types";
import {enumerate} from "@/common/utils";
import {PlayerEventType} from "@/apps/audioplayer/store";
import {Playlist} from "@/api/api";

export type PlaylistType = {
    id: number,
    name: string,
    activeTrackIdx: number,
    playbackPosition: number,
    tracks: TrackInterface[],
}

type PlaylistManagerState = {
    playlists: PlaylistType[],
    activePlaylistIdx: number,
    visiblePlaylistIdx: number,
}

const ADD_FILE_TO_PLAYLIST = 'ADD_FILE_TO_PLAYLIST';
const ADD_YOUTUBE_TO_PLAYLIST = 'ADD_YOUTUBE_TO_PLAYLIST';
const SWAP_TRACK = 'SWAP_TRACK';
const ADD_NEW_PLAYLIST = 'ADD_NEW_PLAYLIST';
const SET_PLAYLIST_ID = 'SET_PLAYLIST_ID';
const SET_ACTIVE_PLAYLIST_IDX = 'SET_ACTIVE_PLAYLIST_IDX';
const SET_VISIBLE_PLAYLIST_IDX = 'SET_VISIBLE_PLAYLIST_IDX';
const SET_ACTIVE_TRACK_IDX_IN_PLAYLIST = 'SET_ACTIVE_TRACK_IDX_IN_PLAYLIST';
const SET_PLAYBACK_POSITION = 'SET_PLAYBACK_POSITION';


const deepcopy = (data: any): any => JSON.parse(JSON.stringify(data));

const AudioPlayerStore: Module<PlaylistManagerState, any> = {
    namespaced: true,
    state () {
        return {
            activePlaylistIdx: 0,
            visiblePlaylistIdx: 0,
            playlists: [
                {
                    id: -1,
                    name: 'New Playlist',
                    activeTrackIdx: 0,
                    playbackPosition: 0,
                    tracks: [],
                }
            ]
        };
    },
    getters: {
        playlists: (state) => state.playlists,
        activePlaylistIdx: (state) => state.activePlaylistIdx,
        visiblePlaylistIdx: (state) => state.visiblePlaylistIdx,
        _visiblePlaylist: (state) => state.playlists[state.visiblePlaylistIdx],
        activePlaylist: (state) => state.playlists[state.activePlaylistIdx],
        activeTrack: (state, getters) => {
            const pl = getters.activePlaylist;
            return pl.tracks[pl.activeTrackIdx];
        },
        activePlaylistHasNextTrack: (state, getters) => {
            const playlist = getters.activePlaylist;
            return playlist.tracks.length - 1 > playlist.activeTrackIdx;
        },
    },
    actions: {
        withUndo: function ({dispatch, getters}, actionFunction) {
            const before = deepcopy(getters._visiblePlaylist);
            const after = getters._visiblePlaylist;
            actionFunction();
            dispatch('playlistChanged', {before, after});
        },
        playlistChanged: async function ({commit}, {before, after}) {
            if (after.id < 0) { // unsaved playlist
                const oldId = after.id
                const savedPlaylist = await Playlist.create(after);
                const newId = savedPlaylist.id;
                commit(SET_PLAYLIST_ID, {oldId, newId});
            } else {
                Playlist.update(after.id, after);
            }
        },
        addNewPlaylist: function ({commit, getters}) {
            commit(ADD_NEW_PLAYLIST);
            commit(SET_VISIBLE_PLAYLIST_IDX, getters.playlists.length - 1);
        },
        addFileToVisiblePlaylist: function ({commit, getters, dispatch}, file) {
            const playlistIdx = getters.visiblePlaylistIdx;
            dispatch('withUndo', () => {
                commit(ADD_FILE_TO_PLAYLIST, {playlistIdx, file});
            });
        },
        addYoutubeToVisiblePlaylist: function ({commit, getters, dispatch}, youtube) {
            const playlistIdx = getters.visiblePlaylistIdx;
            dispatch('withUndo', () => {
                commit(ADD_YOUTUBE_TO_PLAYLIST, {playlistIdx, youtube});
            })
        },
        swapTrackInActivePlaylist: function ({commit, getters, dispatch}, {oldIndex, newIndex}) {
            const playlistIdx = getters.visiblePlaylistIdx;
            dispatch('withUndo', () => {
                commit(SWAP_TRACK, {playlistIdx, oldIndex, newIndex});
            });
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
        },
        playNextTrack: function ({getters, dispatch}) {
            dispatch(
                'play',
                {
                    playlistIdx: getters.activePlaylistIdx,
                    trackIdx: getters.activePlaylist.activeTrackIdx + 1,
                },
            );
        },
        playPreviousTrack: function ({getters, dispatch}) {
            dispatch(
                'play',
                {
                    playlistIdx: getters.activePlaylistIdx,
                    trackIdx: Math.max(0, getters.activePlaylist.activeTrackIdx - 1),
                },
            );
        },
        triggerEndOfPlaylistAction: function () {
            alert('triggerEndOfPlaylistAction not implemented');
        },
        setPlaybackPostion: function ({commit}, position) {
            commit(SET_PLAYBACK_POSITION, position)
        },
        onPlayerEvent ({dispatch, getters, commit}, event) {
            if (event.type === PlayerEventType.Ended) {
                if (getters.activePlaylistHasNextTrack) {
                    dispatch('playNextTrack');
                } else {
                    dispatch('triggerEndOfPlaylistAction')
                }
            } else if (event.type === PlayerEventType.TimeUpdate) {
                commit(
                    SET_PLAYBACK_POSITION,
                    {
                        playbackPosition: event.payload.currentTime,
                        playlistIdx: getters.activePlaylistIdx,
                    },
                );
            }
        },
    },
    mutations: {
        [ADD_FILE_TO_PLAYLIST]: (state, {playlistIdx, file}) => {
            state.playlists[playlistIdx].tracks.push({
                renderId: (Math.random() * 10000000) | 0,
                playlist: null,
                order: state.playlists[playlistIdx].tracks.length,
                type: TrackType.File,
                file: file,
                youtube: null,
            });
        },
        [ADD_YOUTUBE_TO_PLAYLIST]: (state, {playlistIdx, youtube}) => {
            state.playlists[playlistIdx].tracks.push({
                renderId: (Math.random() * 10000000) | 0,
                playlist: null,
                order: state.playlists[playlistIdx].tracks.length,
                type: TrackType.Youtube,
                file: null,
                youtube: youtube,
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
                    tracks: [],
                    playbackPosition: 0,
                }
            ]
        },
        [SET_PLAYLIST_ID]: (state, {oldId, newId}) => {
          state.playlists = state.playlists.map((playlist) => {
              if (playlist.id === oldId) {
                  playlist.id = newId;
              }
              return playlist;
          })
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
        [SET_PLAYBACK_POSITION]: (state, {playlistIdx, playbackPosition}) => {
            state.playlists[playlistIdx].playbackPosition = playbackPosition;
        }
    },
};

export default AudioPlayerStore;
