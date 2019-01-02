<template>
    <div>
        <b-btn @click="searchYoutube()">search yt</b-btn>
        <b-card
            v-for="video in searchResults"
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
            <b-button href="#" variant="primary">
                PLAY
            </b-button>
          </b-card>
    </div>
</template>

<script lang="ts">
    import Vue from "vue";
    import {Youtube} from "@/api/api";

    export default Vue.extend({
        name: 'youtubesearch',
        props: {
        },
        data: function () {
            return {
                searchResults: []
            };
        },
        components: {

        },
        methods: {
          searchYoutube: async function () {
              this.searchResults = await Youtube.search({query: 'gas königsforst'});
          }
        },
    });
</script>

<style scoped>
    .youtube-card > .card-body > .card-title, .youtube-card > .card-body > .card-text {
        background-color: rgba(255,255,255,0.4);
        display: inline;
    }
</style>
