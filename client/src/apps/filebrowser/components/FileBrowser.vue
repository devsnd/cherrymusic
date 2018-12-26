<template>
    <div>
        <template v-if="loading">
            <LoadingAnimation></LoadingAnimation>
        </template>
        <template v-else>
            <b-btn @click="goUp()">
                &lt;--
            </b-btn>
            <Scrollable>
                <div v-if="currentDirectory !== null">
                    <b-list-group>
                        <DirectoryItem
                            @click.native="loadDir(dir.id)"
                            v-for="dir in currentDirectory.sub_directories"
                            :key="dir.id"
                            :directory="dir"
                        ></DirectoryItem>
                    </b-list-group>
                    <b-list-group>
                        <FileItem
                            v-for="file in currentDirectory.files"
                             @click.native="playFile(file)"
                            :file="file"
                            :key="file.id"
                        ></FileItem>
                    </b-list-group>
                </div>
            </Scrollable>
        </template>
    </div>
</template>

<script lang="ts">
    import Vue from 'vue';
    import {Directory} from "@/api/api";
    import FileItem from './FileItem';
    import DirectoryItem from './DirectoryItem';
    import LoadingAnimation from '@/components/LoadingAnimation/LoadingAnimation'
    import {mapActions, mapGetters} from "vuex";
    import Scrollable from '@/containers/Scrollable';

    export default Vue.extend({
        name: '',
        components: {
            LoadingAnimation,
            FileItem,
            DirectoryItem,
            Scrollable,
        },
        computed: {
            ...mapGetters({
                loading: 'filebrowser/loading',
                currentDirectory: 'filebrowser/currentDirectory',
                parentDirectory: 'filebrowser/parentDirectory',
            })
        },
        methods: {
            goUp: function () {
                (this as any).loadDir(this.parentDirectory.id);
            },
            ...mapActions({
                loadDir: 'filebrowser/loadDir',
                playFile: 'audioplayer/playFile',
            })
        }
    });
</script>

<style scoped>

</style>
