<template>
    <div>
        <template v-if="loading">
            <LoadingAnimation></LoadingAnimation>
        </template>
        <template v-else>
            <b-alert show variant="secondary">
                <b-btn @click="goUp()"><i class="fa fa-level-up"></i></b-btn>
                <template v-for="(breadcrumb, idx) in breadcrumbs">
                    <a @click="goTo(breadcrumb.id)" href="#">{{ breadcrumb.path }}</a>
                    <span v-if="idx < breadcrumbs.length - 1"> / </span>
                </template>
            </b-alert>
            <Scrollable :bottom="130">
                <div v-if="currentDirectory !== null">
                    <b-list-group>
                        <DirectoryItem
                            @click.native="loadDir(dir.id)"
                            v-for="dir in currentDirectory.sub_directories"
                            :key="dir.id"
                            :directory="dir"
                        ></DirectoryItem>
                    </b-list-group>
                    <b-btn
                        v-if="currentDirectory.files.length > 0"
                        @click="addFilesToPlaylist(currentDirectory.files)"
                    >
                        Add all files to playlist
                    </b-btn>
                    <b-list-group>
                        <FileItem
                            v-for="file in currentDirectory.files"
                             @click.native="addFileToVisiblePlaylist(file)"
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
    import FileItem from '@/components/common/FileItem';
    import DirectoryItem from './DirectoryItem';
    import LoadingAnimation from '@/components/LoadingAnimation/LoadingAnimation'
    import {mapActions, mapGetters} from "vuex";
    import Scrollable from '@/containers/Scrollable';
    import {FileInterface} from "../../../api/types";

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
                breadcrumbs: 'filebrowser/breadcrumbs',
            }),
        },
        methods: {
            goTo: function (id: number) {
              (this as any).loadDir(id);
            },
            goUp: function () {
                (this as any).loadDir(this.parentDirectory.id);
            },
            addFilesToPlaylist: function (files: FileInterface[]) {
                for (const file of files) {
                    this.addFileToVisiblePlaylist(file);
                }
            },
            ...mapActions({
                loadDir: 'filebrowser/loadDir',
                // playFile: 'audioplayer/playFile',
                addFileToVisiblePlaylist: 'playlist/addFileToVisiblePlaylist',
            })
        }
    });
</script>

<style scoped>

</style>
