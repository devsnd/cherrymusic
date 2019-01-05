<template>
    <b-card no-body>
        <div class="tabs">
            <div class="card-header">
                <ul role="tablist" tabindex="0" class="nav nav-tabs card-header-tabs">
                    <li
                        v-for="(playlist, index) in playlists"
                        :key="playlist.id"
                        role="presentation" class="nav-item"
                    >
                        <a
                            role="tab"
                            tabindex="-1"
                            href="#"
                            aria-selected="true"
                            aria-setsize="2"
                            aria-posinset="1"
                            class="nav-link"
                            :class="{'active': visiblePlaylistIdx === index}"
                            @click="setVisiblePlaylistIdx(index)"
                            @dblclick="setPlaylistTitle(index)"
                        >
                            {{playlist.name}}
                            <span v-if="index === activePlaylistIdx">
                                <i class="fa fa-play"></i>
                            </span>
                        </a>
                    </li>
                    <li key="+" role="presentation" class="nav-item">
                        <a
                            role="tab"
                            tabindex="-1"
                            href="#"
                            aria-selected="true"
                            aria-setsize="2"
                            aria-posinset="1"
                            class="nav-link"
                            @click="addNewPlaylist()"
                        >
                            +
                        </a>
                    </li>
                </ul>
            </div>
            <div class="tab-content">
                <div role="tabpanel" aria-hidden="false" aria-expanded="true" class="tab-pane card-body show fade active">
                    <div v-if="playlists[visiblePlaylistIdx].tracks.length === 0">
                        <translate>This playlist is empty.</translate>
                        <translate>Search or Browse to add tracks.</translate>
                    </div>
                    <Playlist
                        :playlist="playlists[visiblePlaylistIdx]"
                        :triggerPlay="playTrackInPlaylist(visiblePlaylistIdx)"
                    ></Playlist>
                </div>
            </div>
        </div>
        <div class="p-2">
            Once the playlist finishes:
            <select>
                <option>Play next playlist tab</option>
                <option>repeat playlist from the beginning</option>
                <option>do nothing</option>
            </select>
        </div>
    </b-card>
</template>
<script lang="ts">
    import {mapGetters, mapActions} from 'vuex';
    import Playlist from './Playlist';
    import Scrollable from '@/containers/Scrollable';
    import Vue from "vue";

    export default Vue.extend({
        name: 'playlistmanager',
        components: {
            Playlist,
            Scrollable,
        },
        computed: {
            ...mapGetters({
                playlists: 'playlist/playlists',
                activePlaylistIdx: 'playlist/activePlaylistIdx',
                visiblePlaylistIdx: 'playlist/visiblePlaylistIdx',
            }),
        },
        methods: {
            ...mapActions({
                addNewPlaylist: 'playlist/addNewPlaylist',
                setVisiblePlaylistIdx: 'playlist/setVisiblePlaylistIdx',
                play: 'playlist/play',
            }),
            playTrackInPlaylist: function (playlistIdx: number) {
                return (trackIdx: number) => {
                    this.play({playlistIdx, trackIdx});
                }
            },
            setPlaylistTitle: function (e: any) {
                alert('Setting playlist title is not implemented');
            }
        },
    });
</script>
