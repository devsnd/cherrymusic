<template>
  <b-tabs>
    <b-tab
            v-for="(playlist, index) in playlists"
            :key="playlist.id"
            :active="index == activePlaylistIdx"
            :title="playlist.name"
    >
      <Scrollable>
        <Playlist :playlist="playlist"></Playlist>
      </Scrollable>
    </b-tab>
    <b-tab :key="0" @click="addNewPlaylist()" title="+"></b-tab>
  </b-tabs>
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
            }),
        },
        methods: {

        },
    });
</script>
