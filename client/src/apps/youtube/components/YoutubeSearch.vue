<template>
    <div>
        <LoadingAnimation v-if="searching"></LoadingAnimation>
        <SearchResultTile
            v-for="video in results"
            :key="video.youtube_id"
            :img="video.thumbnail_url"
            @click.native="addYoutubeToVisiblePlaylist(video)"
        >
            {{video.title}}<br>
            {{ video.duration }}<br><br>
            {{ video.views }} views<br>
        </SearchResultTile>
    </div>
</template>

<script lang="ts">
    import Vue from "vue";
    import {Youtube} from "@/api/api";
    import {mapActions, mapGetters} from "vuex";
    import LoadingAnimation from '@/components/LoadingAnimation/LoadingAnimation'
    import {YoutubeInterface} from "../../../api/types";
    import SearchResultTile from '@/components/common/SearchResultTile';

    export default Vue.extend({
        name: 'youtubesearch',
        components: {
            LoadingAnimation,
            SearchResultTile,
        },
        computed: {
            ...mapGetters({
                results: 'youtube/results',
                searching: 'youtube/searching',
            })
        },
        methods: {
            addToPlaylist: function (video: YoutubeInterface) {
                this.addYoutubeToVisiblePlaylist(video);
            },
            ...mapActions({
                searchYoutube: 'youtube/search',
                addYoutubeToVisiblePlaylist: 'playlist/addYoutubeToVisiblePlaylist',
            }),
        },
    });
</script>

<style scoped>
    .youtube-card > .card-body > .card-title, .youtube-card > .card-body > .card-text {
        background-color: rgba(255,255,255,0.8);
        display: inline;
    }
</style>
