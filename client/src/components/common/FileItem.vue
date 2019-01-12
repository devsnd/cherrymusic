<template>
    <b-list-group-item
        :active="active"
        variant="secondary"
        class="d-flex justify-content-between align-items-center hover file-item"
        @click="onClick ? onClick() : null"
    >
        <slot name="left"></slot>
        <span style="width: 30px; text-align: right" class="pr-2">{{track}}</span>
        <span class="file-name flex-grow-1">{{prettyFileName}}</span>
        <b-badge variant="dark" pill>{{prettyDuration}}</b-badge>
        <slot name="right"></slot>
    </b-list-group-item>
</template>

<script lang="ts">
    import Vue from 'vue';
    import {FileInterface} from '@/api/types';
    import {formatDuration} from "../../common/utils";

    export default Vue.extend({
        name: '',
        props: [
            'file',
            'active',
            'onClick',
        ],
        computed: {
            track: function () {
                const file = (this.file as FileInterface);
                if (file.meta_data && file.meta_data.track) {
                    return file.meta_data.track;
                }
            },
            prettyFileName: function () {
                const file = (this.file as FileInterface);
                if (file.meta_data === null) {
                    return file.filename;
                }
                return `${file.meta_data.artist.name} - ${file.meta_data.title}`;
            },
            prettyDuration: function () {
                const file = (this.file as FileInterface);
                if (file.meta_data === null || file.meta_data.duration === null) {
                    return '';
                }
                return formatDuration(file.meta_data.duration);
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
