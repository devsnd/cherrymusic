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
      Once the playlist finishes:
      <select>
        <option>Play next playlist tab</option>
        <option>repeat playlist from the beginning</option>
        <option>do nothing</option>
      </select>
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
