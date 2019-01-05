<template>
    <b-list-group-item
        :active="active"
        variant="secondary"
        class="d-flex justify-content-between align-items-center hover file-item"
    >
        <span style="width: 30px; text-align: right" class="pr-2">{{track}}</span>
        <span class="file-name flex-grow-1">{{prettyFileName}}</span>
        <b-badge variant="dark" pill>{{prettyDuration}}</b-badge>
    </b-list-group-item>
</template>

<script lang="ts">
    import Vue from 'vue';
    import {FileInterface} from '@/api/types';
    import {YoutubeInterface} from "../../../api/types";
    import {formatDuration} from "../../../common/utils";

    export default Vue.extend({
        name: '',
        props: [
          'youtube',
          'active',
        ],
        computed: {
            track: function () {
                return '';
            },
            prettyFileName: function () {
                const youtube = (this.youtube as YoutubeInterface);
                return youtube.title;
            },
            prettyDuration: function () {
                const youtube = (this.youtube as YoutubeInterface);
                return formatDuration(youtube.duration);
            }
        }
    });
</script>

<style scoped>
    .file-name {
        max-width: 85%;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .file-item {
        height: 35px;
        white-space: nowrap;
    }
    .hover:hover {
        background-color: #eee;
        cursor: pointer;
    }
</style>
