import {Module} from "vuex";
import {Search} from "@/api/api";
import * as _ from 'lodash';

type SearchResults = any;

type SearchState = {
    results: SearchResults,
    lastQuery: string,
    searching: boolean,
    cache: Map<string, SearchResults>,
}

const SET_SEARCH_RESULTS = 'SET_SEARCH_RESULTS';
const SET_SEARCHING = 'SET_SEARCHING';
const SET_LAST_QUERY = 'SET_LAST_QUERY';

let _debouncedSearch: Function;

const SearchStore: Module<SearchState, any> = {
    namespaced: true,
    state () {
        return {
            results: {
                artists: [],
                albums: [],
                files: [],
            },
            lastQuery: '',
            searching: false,
            cache: new Map<string,SearchResults>(),
        };
    },
    getters: {
        results: (state) => state.results,
        searching: (state) => state.searching,
        cache: (state) => state.cache,
    },
    actions: {
        searchIsCached: function ({getters}, query) {

            return ;
        },
        debouncedSearch: async function ({dispatch, commit, getters}, query: string) {
            query = query.trim();
            if (getters.cache.has(query)) {
                dispatch('search', query);
            } else {
                if (_debouncedSearch === undefined) {
                  _debouncedSearch = _.debounce(
                      (q) => dispatch('search', q),
                      300
                  );
                }
                _debouncedSearch(query);
            }
        },
        search: async function ({dispatch, commit, getters}, query: string) {
            let results = getters.cache.get(query);
            if (results === undefined) {
                commit(SET_SEARCHING, true);
                commit(SET_LAST_QUERY, query);
                results = await Search.search({query: query});
                getters.cache.set(query, results);
            }
            commit(SET_SEARCHING, false);
            commit(SET_SEARCH_RESULTS, results);
        }
    },
    mutations: {
        [SET_SEARCH_RESULTS]: (state, results: SearchResults) => {
            state.results = results;
        },
        [SET_SEARCHING]: (state, searching: boolean) => {
            state.searching = searching;
        },
        [SET_LAST_QUERY]: (state, query: string) => {
            state.lastQuery = query;
        }
    },
};

export default SearchStore;
