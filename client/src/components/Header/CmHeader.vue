<template>
  <b-navbar toggleable="md" type="dark" variant="dark">

    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>

    <b-navbar-brand href="#">CherryMusic</b-navbar-brand>

    <b-collapse is-nav id="nav_collapse">
      <b-nav-form>
        <b-form-input size="sm" class="mr-sm-2" type="text" placeholder="Search" v-model="searchText"/>
        <b-button size="sm" class="my-2 my-sm-0" type="submit">Search</b-button>
      </b-nav-form>

      <b-navbar-nav>
        <b-nav-item href="#" @click="browseFiles()">
          Browse Files
        </b-nav-item>
        <b-nav-item href="#">
          Load Playlist
        </b-nav-item>
      </b-navbar-nav>

      <!-- Right aligned nav items -->
      <b-navbar-nav class="ml-auto">
        <LanguageSwitcher></LanguageSwitcher>

        <b-nav-item-dropdown right>
          <!-- Using button-content slot -->
          <template slot="button-content">
            <span class="fa fa-wrench"></span>
          </template>
          <b-dropdown-item href="#" v-translate>Admin</b-dropdown-item>
          <b-dropdown-item href="#">Options</b-dropdown-item>
        </b-nav-item-dropdown>
      </b-navbar-nav>

    </b-collapse>
  </b-navbar>
</template>
<script lang="ts">
    import Vue from 'vue';
    import LanguageSwitcher from './LanguageSwitcher';
    import {mapActions} from "vuex";

    export default Vue.extend({
        name: 'cm-header',
        data: function () {
            return {
                searchText: '',
            };
        },
        components: {
            LanguageSwitcher,
        },
        computed: {
        },
        methods: {
            browseFiles: function () {
                (this as any).loadDir(1);
            },
            ...mapActions({
                loadDir: 'filebrowser/loadDir',
            })
        }
    });
</script>
