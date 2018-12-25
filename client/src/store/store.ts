import {Vue} from "vue/types/vue";
import Vuex from 'vuex';

Vue.use(Vuex);

// const debug = process.env.NODE_ENV !== 'production';
import api from '@/apps/api/store';

export default new Vuex.Store({
   modules: {
       api: api,
   }
})
