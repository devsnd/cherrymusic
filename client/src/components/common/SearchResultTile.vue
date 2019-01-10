<template>
    <b-card
        overlay
        :img-src="img"
        class="mb-1 mr-1 search-result-card"
        style="width: 160px; height: 160px; display: inline-block"
    >
        <span style="background-color: rgba(255,255,255,0.75);">
            <slot></slot>
        </span>
    </b-card>
</template>

<script lang="ts">
    export default {
        name: 'SearchResultTile',
        props: [
            'img'
        ]

    };
</script>

<style scoped>
    .search-result-card > .card-body {
        text-overflow: ellipsis;
        overflow: hidden;
    }
</style>
