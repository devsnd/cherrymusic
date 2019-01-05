<template>
    <b-list-group v-sortable="{onUpdate: onChangedSorting}">
        <template
            v-for="(track, index) in playlist.tracks"
        >
            <template v-if="track.type === TrackType.File">
                <FileItem
                    :key="track.renderId"
                    :file="track.file"
                    :active="index === playlist.activeTrackIdx"
                    @click.native="playTrack(index)"
                ></FileItem>
            </template>
        </template>
    </b-list-group>

</template>
<script lang="ts">
    interface SortableEvent {
        oldIndex: number,
        newIndex: number,
    }

    import {mapGetters, mapActions} from 'vuex';
    import Vue from "vue";
    import FileItem from '@/components/common/FileItem';
    import {TrackType} from "@/api/types";

    export default Vue.extend({
        name: 'playlist',
        props: {
            'playlist': {
                type: Object
            },
            'triggerPlay': {
                type: Function,
            }
        },
        data: function () {
            return {
                TrackType,
            }
        },
        components: {
            FileItem,
        },
        methods: {
            ...mapActions({
                swapTrackInActivePlaylist: 'playlist/swapTrackInActivePlaylist',
            }),
            playTrack: function (trackIdx: number) {
                this.triggerPlay(trackIdx);
            },
            onChangedSorting: function (event: SortableEvent) {
                const oldIndex = event.oldIndex;
                const newIndex = event.newIndex;
                this.swapTrackInActivePlaylist({oldIndex, newIndex});
            },
        },
        computed: {
            ...mapGetters({}),
        }
    });
</script>
