import {TrackType} from "../../../api/types";
import {TrackType} from "../../../api/types";
<template>
    <div>
        <b-badge :variant="littleTimeLeft ? 'danger' : 'light'" style="display: inline">
            {{elapsedTime | formatDuration}} / {{duration | formatDuration}}
        </b-badge>
        <b-progress :max="duration" style="height: 4px" class="mb-2">
            <b-progress-bar
                    :variant="littleTimeLeft ? 'danger' : 'secondary'"
                    :value="elapsedTime"
            ></b-progress-bar>
        </b-progress>
        <Scrollable :bottom="180" fill>
            <div v-if="playlist.tracks.length === 0">
                <translate>This playlist is empty.</translate>
                <translate>Search or Browse to add tracks.</translate>
            </div>

            <b-list-group v-sortable="{onUpdate: onChangedSorting}">
                <template
                        v-for="(track, index) in playlist.tracks"
                >
                    <template v-if="track.type === TrackType.File">
                        <div
                            :key="track.renderId"
                            :onClick="() => playTrack(index)"
                        >
                            <div>
                                <span class="pl-1">
                                    <i v-if="isAvailableOffline(track.file.id)" class="fa fa-save"></i>
                                    <i
                                            v-if="!isAvailableOffline(track.file.id)"
                                            @click="makeAvailableOffline(track)"
                                            class="fa fa-save"
                                            style="opacity: 0.3"
                                    ></i>
                                </span>
                            </div>
                            <FileItem
                                    :file="track.file"
                                    :active="index === playlist.activeTrackIdx"
                            >
                            </FileItem>
                        </div>
                    </template>
                    <template v-if="track.type === TrackType.Youtube">
                        <YoutubeItem
                                :key="track.renderId"
                                :youtube="track.youtube"
                                :active="index === playlist.activeTrackIdx"
                                @click.native="playTrack(index)"
                        ></YoutubeItem>
                    </template>
                </template>
            </b-list-group>
        </Scrollable>
    </div>
</template>
<script lang="ts">
    import {formatDuration, sum} from "../../../common/utils";
    import {mapActions, mapGetters} from 'vuex';
    import Vue from "vue";
    import FileItem from '@/components/common/FileItem';
    import {TrackType} from "@/api/types";
    import {PlaylistType} from "../store";
    import YoutubeItem from './YoutubeItem';
    import {TrackInterface} from "../../../api/types";
    import Scrollable from '@/containers/Scrollable';
    import {OfflineStoreState} from "../../offline/store";

    interface SortableEvent {
        oldIndex: number,
        newIndex: number,
    }

    function getTrackDurations (tracks: TrackInterface[]) {
        return tracks.map((track) => {
            if (track.type === TrackType.File) {
                return (
                    track.file !== null &&
                    track.file.meta_data !== null &&
                    track.file.meta_data.duration || 0
                );
            } else if (track.type === TrackType.Youtube) {
                return track.youtube && track.youtube.duration || 0;
            }
            return 0;
        })
    }


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
            YoutubeItem,
            Scrollable,
        },
        methods: {
            ...mapActions({
                swapTrackInActivePlaylist: 'playlist/swapTrackInActivePlaylist',
                addToOfflineTracks: 'offline/addToOfflineTracks',
            }),
            playTrack: function (trackIdx: number) {
                this.triggerPlay(trackIdx);
            },
            onChangedSorting: function (event: SortableEvent) {
                const oldIndex = event.oldIndex;
                const newIndex = event.newIndex;
                (this as any).swapTrackInActivePlaylist({oldIndex, newIndex});
            },
            isAvailableOffline: function (fileId: number): boolean {
                return (this as any).offlineTrackIds.indexOf(fileId) !== -1;
            },
            makeAvailableOffline: async function (track: TrackInterface) {
                if (track.file === null) {
                    throw new Error('Cannot make track available offline, it does not have a `file`')
                }
                const response: Response = await fetch(track.file.stream_url);
                const data = await response.blob();
                (this as any).addToOfflineTracks({track: track, data: data});
            }
        },
        computed: {
            duration: function () {
                const playlist = (this.playlist as PlaylistType);
                const tracksDurations = getTrackDurations(playlist.tracks);
                if (tracksDurations.length === 0) {
                    return 0
                }
                const durationSum = sum(tracksDurations);
                const avgDuration = durationSum / tracksDurations.length;
                const unestimated = playlist.tracks.length - tracksDurations.length;
                return durationSum + unestimated * avgDuration;
            },
            elapsedTime: function () {
                const playlist = (this.playlist as PlaylistType);
                const trackDurations = getTrackDurations(playlist.tracks.slice(0, playlist.activeTrackIdx));
                return sum(trackDurations) + playlist.playbackPosition;
            },
            remainingTime: function () {
                return this.duration - this.elapsedTime;
            },
            littleTimeLeft: function () {
                return this.remainingTime < 300;
            },
            ...mapGetters({
                offlineTrackIds: 'offline/offlineTrackIds',
            }),
        },
        filters: {
            formatDuration: formatDuration,
        },
    });
</script>
