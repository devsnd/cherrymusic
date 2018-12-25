<template>
    <div>
        <b-btn @click="listDirs()">list files</b-btn>
        <div v-if="directory">
            <b-btn @click="loadDir(dir.id)" v-for="dir in directory.sub_directories">
                {{dir}}
            </b-btn>
            <ul>
                <li v-for="file in directory.files">
                    {{file}}
                </li>
            </ul>
        </div>
    </div>
</template>

<script lang="ts">
    import Vue from 'vue';
    import {Directory} from "../../api/api";

    export default Vue.extend({
        name: '',
        data: function () {
            return {
                directory: null,
            }
        },
        methods: {
            listDirs: async function () {
                this.directory = await Directory.read(1);
            },
            loadDir: async function (id) {
                this.directory = await Directory.read(id);
            }

        }
    });
</script>

<style scoped>

</style>
