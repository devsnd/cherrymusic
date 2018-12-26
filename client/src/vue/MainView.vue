<template>
    <div>
        <b-container>
            <cm-header></cm-header>
            <b-row>
                <b-col style="max-width: 50%" class="mt-2">
                    <file-browser></file-browser>
                </b-col>
                <b-col style="max-width: 50%" class="mt-2">
                    <PlaylistManager></PlaylistManager>
                </b-col>
            </b-row>
            <Audioplayer></Audioplayer>
        </b-container>
    </div>
</template>

<script lang="ts">
    import { mapGetters } from 'vuex';
    import PlaylistManager from '@/apps/playlist/components/PlaylistManager';
    import Audioplayer from '@/apps/audioplayer/components/Audioplayer';
    import CmHeader from '@/components/Header/CmHeader';
    import FileBrowser from '@/apps/filebrowser/components/FileBrowser';
    import Vue from "vue";

    export default Vue.extend({
        name: 'dashboard',
        props: {
        },
        components: {
            PlaylistManager,
            CmHeader,
            FileBrowser,
            Audioplayer,
        },
        computed: {
            ...mapGetters({

            })
        }
    });
</script>
