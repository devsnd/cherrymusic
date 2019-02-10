<template>
    <b-container fluid style="max-width: 1200px">
        <slot></slot>
    </b-container>
</template>
<script lang="ts">
    import Vue from 'vue';

    export default Vue.extend({
        name: 'cm-container',
    });
</script>
