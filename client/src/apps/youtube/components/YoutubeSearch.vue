<template>
    <div>
        <LoadingAnimation v-if="searching"></LoadingAnimation>
        <b-btn @click="searchYoutube()">search yt</b-btn>
        <b-card
            v-for="video in results"
            :key="video.youtube_id"
            :img-src="video.thumbnail_url"
            :title="video.title"
            :img-alt="video.title"
            overlay
            class="mb-2 youtube-card"
        >
            <p class="card-text">
                <br>
                {{ video.duration }}<br><br>
                {{ video.views }} views<br>
                {{ video.youtube_id }}
            </p>
            <b-btn variant="primary" @click="addToPlaylist(video)">
                PLAY
            </b-btn>
          </b-card>
    </div>
</template>

<script lang="ts">
    import Vue from "vue";
    import {Youtube} from "@/api/api";
    import {mapActions, mapGetters} from "vuex";
    import LoadingAnimation from '@/components/LoadingAnimation/LoadingAnimation'
    import {YoutubeInterface} from "../../../api/types";

    export default Vue.extend({
        name: 'youtubesearch',
        components: {
            LoadingAnimation,
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
        background-color: rgba(255,255,255,0.4);
        display: inline;
    }
</style>
