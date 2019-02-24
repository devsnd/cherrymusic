<template>
  <b-modal id="optionsModal">
      <h3>Offline Storage</h3>
      <b-btn @click="clearOfflineStorage()">Delete all offline stored tracks from this device</b-btn>
  </b-modal>
</template>

<script lang="ts">
import Vue from "vue";
import {mapActions} from "vuex";

export default Vue.extend({
    name: 'optionsmodal',
    methods: {
        ...mapActions({
            clearOfflineStorage: 'offline/clearStorage'
        })
    },
});
</script>

<style>
.greeting {
    font-size: 20px;
}
</style>
