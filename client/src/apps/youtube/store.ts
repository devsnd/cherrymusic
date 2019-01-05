import {Module} from "vuex";
import {Youtube} from "@/api/api";
import {YoutubeInterface} from "@/api/types";

type YoutubeSearchState = {
    searching: boolean,
    query: string,
    results: YoutubeInterface[],
}

const SET_SEARCHING = 'SET_SEARCHING';
const SET_RESULTS = 'SET_RESULTS';
const SET_QUERY = 'SET_QUERY';

const YoutubeSearchStore: Module<YoutubeSearchState, any> = {
    namespaced: true,
    state () {
        return {
            query: '',
            searching: false,
            results: [],
        };
    },
    getters: {
        query: (state) => state.query,
        searching: (state) => state.searching,
        results: (state) => state.results,
    },
    actions: {
        search: async function ({commit}, query) {
            commit(SET_SEARCHING, true);
            commit(SET_QUERY, query);
            const results = await Youtube.search({query: query});
            commit(SET_RESULTS, results);
            commit(SET_SEARCHING, false);
        }
    },
    mutations: {
        [SET_SEARCHING]: (state, searching) => {
            state.searching = searching;
        },
        [SET_RESULTS]: (state, results) => {
            state.results = results;
        },
        [SET_QUERY]: (state, query) => {
            state.query = query;
        },
    },
};

export default YoutubeSearchStore;
