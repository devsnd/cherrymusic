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
  data: function () {
    return {
      activePlaylistIdx: 0,
      playlists: [
        {
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
  methods: {
    ...mapActions({}),
    addNewPlaylist: function () {
      this.playlists.push(
        {
          id: Math.round(Math.random() * 100000),
          name: 'SCHUallls',
          activeTrack: 2,
          tracks: [
            {'title': 'asd424w3r'},
            {'title': 'asd2qe23ra'},
            {'title': 'agsar436 sfdg>gsd'},
          ]
        }
      );
    }
  },
  computed: {
    ...mapGetters({}),
  }
});
</script>
