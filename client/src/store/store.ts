import Vuex from 'vuex';
import Vue from 'vue';

Vue.use(Vuex);


import filebrowser from '@/apps/filebrowser/store';
import audioplayer from '@/apps/audioplayer/store';
import playlist from '@/apps/playlist/store';


export default new Vuex.Store({
    modules: {
        filebrowser,
        audioplayer,
        playlist,
    }
})
