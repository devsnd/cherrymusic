import Vuex from 'vuex';
import Vue from 'vue';
import filebrowser from '@/apps/filebrowser/store';
import audioplayer from '@/apps/audioplayer/store';
import playlist from '@/apps/playlist/store';
import search from '@/apps/search/store';
import youtube from '@/apps/youtube/store';
import mainview from '@/apps/mainview/store';
import shortcuts from '@/apps/shortcuts/store';
import offline from '@/apps/offline/store';

Vue.use(Vuex);


export default new Vuex.Store({
    modules: {
        audioplayer,
        filebrowser,
        mainview,
        offline,
        playlist,
        search,
        shortcuts,
        youtube,
    }
})
