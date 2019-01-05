<template>
    <div class="scrollable">
        <slot></slot>
    </div>
</template>

<script lang="ts">
    import Vue from 'vue';

    export default Vue.extend({
        name: ''
    });
</script>

<style scoped>
    .scrollable {
        max-height: 500px;
        overflow-y: scroll;
    }
</style>
