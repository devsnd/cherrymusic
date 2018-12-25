<template>
  <b-list-group>
    <b-list-group-item
      class="pt-2 pb-2"
      v-for="(track, index) in playlist.tracks"
      :key="index"
      :active="index == playlist.activeTrack"
    >
      {{ track.title }}
    </b-list-group-item>
</b-list-group>

</template>
<script lang="ts">
import {mapGetters, mapActions} from 'vuex';
import Vue from "vue";

export default Vue.extend({
  name: 'playlist',
  props: {
    'playlist': {
      type: Object
    }
  },
  components: {},
  methods: {
    ...mapActions({})
  },
  computed: {
    ...mapGetters({}),
  }
});
</script>
