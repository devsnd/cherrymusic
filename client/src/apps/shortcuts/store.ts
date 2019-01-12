import {Module} from "vuex";


type MainState = {

}


const MainViewStore: Module<MainState, any> = {
    namespaced: true,
    state () {
        return {
        };
    },
    getters: {
    },
    actions: {
        init: function ({dispatch}) {
            document.onkeyup = function(e) {
                dispatch('onKeyUp', e)
            }
        },
        onKeyUp: function ({dispatch}, e: KeyboardEvent) {
            if (e.key === 'f') {
                const searchField = document.querySelector('#header-search-field');
                if (searchField === null) {
                    console.error('Cannot find search field, cannot focus it!');
                    return;
                }
                (searchField as HTMLElement).focus();
            }
        }
    },
    mutations: {
    },
};

export default MainViewStore;
