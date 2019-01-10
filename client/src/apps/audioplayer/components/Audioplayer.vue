<template>
    <div class="audioplayer bg-secondary">
        <b-container>
            <b-row>
                <b-col>
                    {{currentPlaytime | formatDuration}} / {{duration | formatDuration}}
                    <b-progress
                        :value="currentPlaytime"
                        :max="duration"
                        class="playback-bar"
                        @click.native="onProgressBarClick"
                    ></b-progress>
                </b-col>
            </b-row>
            <b-row>
                <b-col style="text-align: center">
                    <b-btn>
                        <span class="fa fa-2x fa-step-backward"></span>
                    </b-btn>
                    <b-btn>
                        <span class="fa fa-3x fa-pause-circle"></span>
                    </b-btn>
                    <b-btn>
                        <span class="fa fa-3x fa-play-circle"></span>
                    </b-btn>
                    <b-btn>
                        <span class="fa fa-2x fa-step-forward"></span>
                    </b-btn>
                </b-col>
            </b-row>
        </b-container>
    </div>
</template>

<script lang="ts">
    import Vue from 'vue';
    import {mapActions, mapGetters} from "vuex";
    import {formatDuration} from "../../../common/utils";
    export default Vue.extend({
        name: '',
        mounted () {
            this.init();
        },
        computed: {
            ...mapGetters({
                currentPlaytime: 'audioplayer/currentPlaytime',
                duration: 'audioplayer/duration',
                pause: 'audioplayer/pause',
                resume: 'audioplayer/resume',
                nextTrack: 'playlist/playNextTrack',
                previousTrack: 'playlist/playPreviousTrack',
            })
        },
        filters: {
            formatDuration: formatDuration,
        },
        methods: {
            ...mapActions({
                jumpToPercentage: 'audioplayer/jumpToPercentage',
                init: 'audioplayer/init',
            }),
            onProgressBarClick: function (e: MouseEvent) {
                const target = (e.currentTarget as Element);
                const percentage = e.layerX / target.clientWidth;
                this.jumpToPercentage(percentage);
            }
        },
    });
</script>

<style scoped>
    .playback-bar {
        cursor: pointer;
    }
    .audioplayer {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        height: 100px;
        z-index: 10;
    }
</style>
