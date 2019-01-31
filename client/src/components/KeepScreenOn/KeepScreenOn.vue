<template>
    <div>
        <b-checkbox v-model="keepScreenOn">Keep Screen On</b-checkbox>
        <!-- this image is just to get webpack to copy the video for me, something something fileloader -->
        <img style="visibility: hidden" src="../../static/img/logo_video.png"></img>
        <video class="hideVideo" src="../../static/client/logo_video.png" loop="loop" ref="loopVideo"></video>
    </div>
</template>
<style scoped>
    .hideVideo {
        width: 1px;
        height: 1px;
        opacity: 0.01;
        pointer-events: none;
    }
</style>
<script lang="ts">
    import Vue from 'vue';

    export default Vue.extend({
        name: 'keepscreenon',
        mounted: function () {
          this.videoTag = this.$refs.loopVideo;
        },
        watch: {
            keepScreenOn: function (keepItOn) {
                if (keepItOn) {
                    this.videoTag.play();
                    console.log(this.videoTag);
                } else {
                    this.videoTag.pause();
                }
            }
        },
        data: function () {
            return {
                videoTag: null,
                keepScreenOn: false,
            }
        }
    });
</script>
