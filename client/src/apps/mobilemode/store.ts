import {Module} from "vuex";

export type StoreState = {
    isMobile: boolean,
    forceIsMobile: boolean | null,
}

const SET_MOBILE = 'SET_MOBILE';

const OfflineStore: Module<StoreState, any> = {
    namespaced: true,
    state () {
        return {
            isMobile: false,
            forceIsMobile: true,
        };
    },
    getters: {
        isMobile: (state) => state.forceIsMobile !== null ? state.forceIsMobile : state.isMobile,
    },
    actions: {
        init: function ({commit}) {
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            commit(SET_MOBILE, isMobile);
        },
    },
    mutations: {
        [SET_MOBILE]: (state, isMobile) => {
            state.isMobile = isMobile;
        },
    },
};

export default OfflineStore;
