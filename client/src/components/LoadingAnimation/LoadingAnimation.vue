<template>
  <div :class="{'overlay': overlay}">
    <div :class="{'floating': floating}">
      <div class="loading-animation"></div>
    </div>
  </div>
</template>
<style>
  .floating {
    position: absolute;
    left: 50%;
    margin-left: -25px;
    top: 50%;
    margin-top: -25px;
  }
  .overlay {
    z-index: 1000;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255,255,255,0.8);
  }

  .loading-animation {
    background-image: url('./cherrymusic_loader.gif');
    width: 80px;
    height: 80px;
    display: inline-block;
  }

</style>
<script lang="ts">
import Vue from 'vue';

export default Vue.extend({
  name: 'loadinganimation',
  props: {
    floating: {
      type: Boolean,
      default: false,
    },
    overlay: {
      type: Boolean,
      default: false,
    }
  }
});
</script>
