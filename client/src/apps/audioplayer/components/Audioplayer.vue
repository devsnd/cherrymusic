<template>
    <div class="audioplayer bg-secondary">
        <b-container fluid style="max-width: 1200px">
            <b-row>
                <b-col>
                    <div style="position: relative">
                        <span style="text-align: center; position: absolute; width: 100%">
                            {{currentPlaytime | formatDuration}} / {{duration | formatDuration}}
                        </span>
                        <b-progress
                            :value="currentPlaytime"
                            :max="duration"
                            class="playback-bar mt-1"
                            @click.native="onProgressBarClick"
                        ></b-progress>
                    </div>
                </b-col>
            </b-row>
            <b-row>
                <b-col style="text-align: center">
                    <b-btn @click="previousTrack()">
                        <span class="fa fa-2x fa-step-backward"></span>
                    </b-btn>
                    <b-btn @click="pause()">
                        <span class="fa fa-3x fa-pause-circle"></span>
                    </b-btn>
                    <b-btn @click="resume()">
                        <span class="fa fa-3x fa-play-circle"></span>
                    </b-btn>
                    <b-btn @click="nextTrack()">
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
        components: {
        },
        computed: {
            ...mapGetters({
                currentPlaytime: 'audioplayer/currentPlaytime',
                duration: 'audioplayer/duration',
            })
        },
        filters: {
            formatDuration: formatDuration,
        },
        methods: {
            ...mapActions({
                pause: 'audioplayer/pause',
                resume: 'audioplayer/resume',
                nextTrack: 'playlist/playNextTrack',
                previousTrack: 'playlist/playPreviousTrack',
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
        height: 25px;
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
