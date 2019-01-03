import Vuex from 'vuex';
import Vue from 'vue';

Vue.use(Vuex);


import filebrowser from '@/apps/filebrowser/store';
import audioplayer from '@/apps/audioplayer/store';
import playlist from '@/apps/playlist/store';
import search from '@/apps/search/store';
import mainview from '@/apps/mainview/store';


export default new Vuex.Store({
    modules: {
        filebrowser,
        audioplayer,
        playlist,
        mainview,
        search,
    }
})
