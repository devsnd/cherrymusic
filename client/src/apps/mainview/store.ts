import {Module} from "vuex";

type ViewMode = 'motd' | 'browse' | 'search' | 'ytsearch';

type MainState = {
    viewMode: ViewMode,
}

const SET_VIEWMODE = 'SET_VIEWMODE';

const MainViewStore: Module<MainState, any> = {
    namespaced: true,
    state () {
        return {
            viewMode: 'motd',
        };
    },
    getters: {
        viewMode: (state) => state.viewMode,
    },
    actions: {
        setViewMode: function ({commit}, viewMode: ViewMode) {
            commit(SET_VIEWMODE, viewMode);
        }
    },
    mutations: {
        [SET_VIEWMODE]: (state, viewMode: ViewMode) => {
            state.viewMode = viewMode;
        },
    },
};

export default MainViewStore;
