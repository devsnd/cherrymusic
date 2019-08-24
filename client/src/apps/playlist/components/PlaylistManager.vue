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
                    <Playlist
                        :playlist="playlists[visiblePlaylistIdx]"
                        :triggerPlay="playTrackInPlaylist(visiblePlaylistIdx)"
                    >
                        <template slot="playlist-actions">
                            <div style="width: 100%; position: relative; float: left;">
                                <div style="width: 100%; position: absolute; text-align: right; margin-top: -10px">
                                    <b-btn
                                        size="sm"
                                        @click="makeAllAvailableOffline(playlists[visiblePlaylistIdx].tracks)"
                                    >
                                        <i class="fa fa-save"></i> <i class="fa fa-plane"></i>
                                    </b-btn>
                                    <b-btn
                                        size="sm"
                                        @click="closePlaylist(playlists[visiblePlaylistIdx].id)"
                                    >
                                        &times;
                                    </b-btn>
                                </div>
                            </div>
                        </template>
                    </Playlist>
                </div>
            </div>
        </div>
        <div class="p-2">
            At the end of the list
            <b-dropdown id="ddown-dropup" dropup text="Play next playlist tab" variant="secondary" class="m-2" size="sm">
                <b-dropdown-item>Play next playlist tab</b-dropdown-item>
                <b-dropdown-item>Repeat playlist</b-dropdown-item>
                <b-dropdown-item selected="selected">do nothing</b-dropdown-item>
            </b-dropdown>
        </div>
    </b-card>
</template>
<script lang="ts">
    import {mapGetters, mapActions} from 'vuex';
    import Playlist from './Playlist';
    import Scrollable from '@/containers/Scrollable';
    import Vue from "vue";
    import {TrackInterface} from "@/api/types";

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
                closePlaylist: 'playlist/closePlaylist',
                makeAvailableOffline: 'offline/makeAvailableOffline',
            }),
            playTrackInPlaylist: function (playlistIdx: number) {
                return (trackIdx: number) => {
                    this.play({playlistIdx, trackIdx});
                }
            },
            setPlaylistTitle: function (e: any) {
                alert('Setting playlist title is not implemented');
            },
            makeAllAvailableOffline: function (tracks: TrackInterface[]) {
              for (const track of tracks) {
                (this as any).makeAvailableOffline(track);
              }
            },
        },
    });
</script>
