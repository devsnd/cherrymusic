<template>
  <div>
    <b-container>
      <cm-header></cm-header>
      <b-row>
        <b-col>
          <file-browser></file-browser>
        </b-col>
        <b-col>
          <PlaylistManager></PlaylistManager>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script lang="ts">
    import { mapGetters } from 'vuex';
    import PlaylistManager from '@/components/PlaylistManager/PlaylistManager';
    import CmHeader from '@/components/Header/CmHeader';
    import FileBrowser from '@/components/FileBrowser/FileBrowser';
    import Vue from "vue";

    export default Vue.extend({
        name: 'dashboard',
        props: {
        },
        components: {
            PlaylistManager,
            CmHeader,
            FileBrowser,
        },
        computed: {
            ...mapGetters({

            })
        }
    });
</script>
