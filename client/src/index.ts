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
import GetTextPlugin from 'vue-gettext'
import translations from './translations.json'
Vue.use(GetTextPlugin, {
    translations: translations,
    availableLanguages: {
        'en_US': 'English',
        'de_DE': 'Deutsch',
    }
});

import store from '@/store/store';


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
