<template>
    <div>
        <LoadingAnimation v-if="searching"></LoadingAnimation>
        <div v-if="!searching && noResults">
            <h3><translate>No search results.</translate></h3>
            <br>
            <p>You can try searching on youtube.</p>
            <b-btn @click="showYoutubeSearch()" variant="primary">
                Search on youtube
            </b-btn>
        </div>
        <div v-if="results.artists.length">
            <h3>Artists</h3>
            <div>
                <b-card
                    v-for="artist in results.artists"
                    overlay
                    :key="artist.id"
                    :img-src="defaultImage"
                    class="mb-1 mr-1 artist-card"
                    style="width: 160px; height: 160px; display: inline-block"
                >
                    <span style="background-color: rgba(255,255,255,0.75);">
                        {{artist.name}}
                        <div v-for="b64 in artist.album_thumbnail_gif_b64">
                            <img :src="b64" style="width: 30px">
                        </div>
                    </span>
                </b-card>
            </div>
        </div>
        <div v-if="results.albums.length">
            <h3>Albums</h3>
            <b-card
                v-for="album in results.albums"
                overlay
                :key="album.id"
                :img-src="album.thumbnail_gif_b64 ? album.thumbnail_gif_b64 : defaultImage"
                class="mb-1 mr-1 album-card"
                style="width: 160px; height: 160px; display: inline-block"
            >
                <span style="background-color: rgba(255,255,255,0.75);">
                    {{album.name}}<br><br>
                    by {{album.albumartist.name}}
                </span>
            </b-card>
        </div>
        <div v-if="results.files.length">
            <h3>Songs</h3>
            <b-list-group>
                <FileItem
                    v-for="file in results.files"
                    @click.native="addFileToVisiblePlaylist(file)"
                    :file="file"
                    :key="file.id"
                ></FileItem>
            </b-list-group>
        </div>
    </div>
</template>

<script lang="ts">
    import Vue from 'vue';
    import {mapActions, mapGetters} from 'vuex';
    import LoadingAnimation from '@/components/LoadingAnimation/LoadingAnimation';
    import FileItem from '@/components/common/FileItem';

    export default Vue.extend({
        name: '',
        components: {
            LoadingAnimation,
            FileItem,
        },
        data: function () {
            return {
                defaultImage: 'https://picsum.photos/400/400/?image=36',
            };
        },
        computed: {
            ...mapGetters({
                searching: 'search/searching',
                results: 'search/results',
            }),
            noResults: function (): boolean {
                const vm = (this as any);
                return (
                    !vm.searching &&
                    vm.results.artists.length === 0 &&
                    vm.results.albums.length === 0 &&
                    vm.results.files.length === 0
                );
            }
        },
        methods: {
            ...mapActions({
                addFileToVisiblePlaylist: 'playlist/addFileToVisiblePlaylist',
                setViewMode: 'mainview/setViewMode',
            }),
            showYoutubeSearch: function () {
                (this as any).setViewMode('ytsearch');
            }

        }
    });
</script>

<style scoped>
    .album-card > .card-body, .artist-card > .card-body {
        text-overflow: ellipsis;
        overflow: hidden;
    }
</style>
