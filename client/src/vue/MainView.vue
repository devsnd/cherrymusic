<template>
    <div>
        <b-container>
            <cm-header></cm-header>
            <b-row>
                <b-col style="max-width: 50%" class="mt-2">
                    <div v-if="viewMode === 'motd'">
                        <b-jumbotron
                            header="Cherry Music II"
                            lead="Oh My Gaush, it's finally here" >
                            <p>
                                Kapow!
                            </p>
                        </b-jumbotron>
                    </div>
                    <div v-else-if="viewMode === 'browse'">
                        <file-browser></file-browser>
                    </div>
                    <div v-else-if="viewMode === 'search'">

                    </div>
                    <div v-else-if="viewMode === 'ytsearch'">
                        <youtube-search></youtube-search>
                    </div>
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
    import YoutubeSearch from '@/apps/youtube/components/YoutubeSearch'
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
            YoutubeSearch,
        },
        computed: {
            ...mapGetters({
                viewMode: 'mainview/viewMode'
            })
        }
    });
</script>
