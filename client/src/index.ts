import Vue from "vue";
import MainView from "./vue/MainView.vue";

import BootstrapVue from 'bootstrap-vue'

// enable bootstrap vuew
Vue.use(BootstrapVue);
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';

// add font awesome
import 'font-awesome/css/font-awesome.css';

// enable vue gettext
import VueGettext from 'vue-gettext'
import translations from './translations.json'
Vue.use(VueGettext, {
    translations: translations,
    availableLanguages: {
        'en_US': 'English',
        'de_DE': 'Deutsch',
    },
    silent: true,
});

// enable v-sortable directive for the playlist
//@ts-ignore there are no type definitions for vue-sortable
import Sortable from '@/lib/sortable/vue-sortable';
Vue.use(Sortable);

import store from '@/store/store';
import {PlayerEvent} from "@/apps/audioplayer/store";

// hook up the playlist to the audio player
store.dispatch(
    'audioplayer/addPlayerListener',
    (e: PlayerEvent) => store.dispatch('playlist/onPlayerEvent', e)
);
// load the list of offline tracks
store.dispatch('offline/init');
// detect if we should use mobile mode
store.dispatch('mobilemode/init');

// initialize the api with a new auth token. This should be done in a login view later
import {Settings} from '@/api/api';
Settings.setAuthtoken('47e7f3ca7a06b2d0ab86d6c6734426bbf1ebaef4');

let v = new Vue({
    el: "#app",
    template: `
    <div>
        <main-view></main-view>
    </div>
    `,
    data: { name: "World" },
    store: store,
    components: {
        MainView,
    }
});
