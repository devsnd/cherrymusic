<template>
    <b-list-group-item
        class="d-flex justify-content-between align-items-center hover"
    >
        {{directory.path}}
    </b-list-group-item>
</template>

<script lang="ts">
    import Vue from 'vue';
    import {DirectoryInterface} from "@/api/types";

    export default Vue.extend({
        name: '',
        props: {
            directory: Object as () => DirectoryInterface,
        },
        computed: {
        }
    });
</script>

<style scoped>
    .hover:hover {
        background-color: #eee;
    }
</style>
