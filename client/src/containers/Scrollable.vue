<template>
    <div class="scrollable" ref="scrollable" :style="scrollableStyle">
        <slot></slot>
    </div>
</template>

<script lang="ts">
    import Vue from 'vue';

    export default Vue.extend({
        name: '',
        props: {
          bottom: {
              type: Number,
              default: 0,
          },
          fill: {
              type: Boolean,
              default: false,
          }
        },
        data: function () {
          return {
              viewportHeight: 1000,
              viewportWidth: 1000,
              width: 1000,
              height: 1000,
              x: 0,
              y: 0,
          }
        },
        computed: {
            maxHeight: function () {
                return `${this.viewportHeight - this.y - this.bottom}px`;
            },
            scrollableStyle: function () {
                let scrollableStyle: any = {'max-height': this.maxHeight};
                if (this.fill) {
                    scrollableStyle['min-height'] = this.maxHeight;
                }
                return scrollableStyle;
            }
        },
        methods: {
            updateMesurement: function () {
                const that = (this as any);
                that.viewportHeight = document.documentElement.clientHeight;
                that.viewportWidth = document.documentElement.clientWidth;
                const elem = (this as any).$refs.scrollable;
                const rect = elem.getBoundingClientRect();
                that.height = rect.height;
                that.width = rect.width;
                that.x = rect.x;
                that.y = rect.y;

            }
        },
        mounted: function () {
            (this as any).updateMesurement();
            window.addEventListener('resize', (this as any).updateMesurement);
        }
    });
</script>

<style scoped>
    .scrollable {
        overflow-y: scroll;
    }
</style>
