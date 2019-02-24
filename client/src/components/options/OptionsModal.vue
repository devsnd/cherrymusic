<template>
    <div>
        <b-modal id="optionsModal">
            <h3>Offline Storage</h3>
            <b-btn @click="clearOfflineStorage()">Delete all offline stored tracks from this device</b-btn>
            <h3>Keep Screen On</h3>
            <KeepScreenOn></KeepScreenOn>
        </b-modal>
    </div>
</template>

<script lang="ts">
    import Vue from "vue";
    import {mapActions} from "vuex";
    import KeepScreenOn from '@/components/KeepScreenOn/KeepScreenOn';

    export default Vue.extend({
        name: 'optionsmodal',
        components: {
            KeepScreenOn
        },
        methods: {
            ...mapActions({
                clearOfflineStorage: 'offline/clearStorage'
            })
        },
    });
</script>

<style>
    .greeting {
        font-size: 20px;
    }
</style>
