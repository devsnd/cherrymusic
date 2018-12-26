<template>
    <div class="audioplayer bg-secondary">
        <b-container>
            <b-row>
                <b-col>
                    <audio ref="audiotag"></audio>
                    {{currentPlaytime}} / {{duration}}
                    <b-progress :value="currentPlaytime" :max="duration"></b-progress>
                </b-col>
            </b-row>
        </b-container>
    </div>
</template>

<script lang="ts">
    import Vue from 'vue';
    import {mapActions, mapGetters} from "vuex";
    export default Vue.extend({
        name: '',
        mounted: function () {
            this.registerAudioTag(this.$refs.audiotag);
        },
        computed: {
            ...mapGetters({
                currentPlaytime: 'audioplayer/currentPlaytime',
                duration: 'audioplayer/duration',
            })
        },
        methods: {
            ...mapActions({
                registerAudioTag: 'audioplayer/registerAudioTag',
            })
        }
    });
</script>

<style scoped>
    .audioplayer {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        height: 100px;
    }
</style>
