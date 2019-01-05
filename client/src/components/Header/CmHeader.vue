<template>
  <b-navbar toggleable="md" type="dark" variant="dark">

    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>

    <b-navbar-brand href="#">CherryMusic</b-navbar-brand>

    <b-collapse is-nav id="nav_collapse">
      <b-nav-form @submit="search">
        <b-input-group>
          <b-form-input
            size="sm"
            type="text"
            :placeholder="this.$gettext('Search')"
            :formatter="searchWhileTyping"
            v-model="searchText"
            :disabled="searching"
          />
          <b-input-group-append>
            <b-button size="sm" class="my-2 my-sm-0" @click="search()">
              <translate>
                Search
              </translate>
            </b-button>
          </b-input-group-append>
        </b-input-group>
      </b-nav-form>

      <b-navbar-nav>
        <b-nav-item href="#" @click="browseFiles()">
          <translate>
            Browse Files
          </translate>
        </b-nav-item>
        <b-nav-item href="#">
          <translate>
            Load Playlist
          </translate>
        </b-nav-item>
      </b-navbar-nav>

      <!-- Right aligned nav items -->
      <b-navbar-nav class="ml-auto">
        <LanguageSwitcher></LanguageSwitcher>

        <b-nav-item-dropdown right class="p-0">
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
                searching: false,
            };
        },
        components: {
            LanguageSwitcher,
        },
        computed: {
        },
        methods: {
            search: async function (e?: Event) {
                if (e) {
                  e.preventDefault();
                }
                (this as any).setViewMode('search');
                (this as any).debouncedSearch(this.searchText);
            },
            searchWhileTyping: function (value: string, event: Event) {
              if (event && event.type === 'change') {
                // omit blur and focus events
                return value;
              }
              this.search();
              return value;
            },
            browseFiles: function () {
                (this as any).setViewMode('browse');
                // -1 is the id of the virtual basedirs folder that contains
                // all the base dirs
                (this as any).loadDir(-1);
            },
            ...mapActions({
                loadDir: 'filebrowser/loadDir',
                debouncedSearch: 'search/debouncedSearch',
                searchIsCached: 'search/searchIsCached',
                setViewMode: 'mainview/setViewMode',
            })
        }
    });
</script>
