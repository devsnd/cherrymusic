import {Module} from "vuex";
import {Directory} from "@/api/api";
import {DirectoryInterface} from "@/api/types";

const SET_LOADING = 'SET_LOADING';
const UPDATE_DIRECTORY = 'UPDATE_DIRECTORY';
const SET_CURRENT_DIRECTORY_ID = 'SET_CURRENT_DIRECTORY_ID';
const SET_PARENT_DIRECTORY_ID = 'SET_PARENT_DIRECTORY_ID';


type FileBrowserState = {
    loading: boolean,
    currentId: null | number,
    parentId: null | number,
    directoryById: {[key: number]: DirectoryInterface}
}

const FileBrowserStore: Module<FileBrowserState, any> = {
    namespaced: true,
    state () {
        return {
            loading: false,
            currentId: null,
            parentId: null,
            directoryById: {},
        };
    },
    getters: {
        loading: (state) => state.loading,
        currentDirectory: (state) => state.currentId === null ? null : state.directoryById[state.currentId],
        parentDirectory: (state) => state.parentId === null ? null : state.directoryById[state.parentId],
    },
    actions: {
        async loadDir ({commit, state}, id: number) {
            if (state.directoryById[id] === undefined) {
                commit(SET_LOADING, true);
                const directory: DirectoryInterface = await Directory.read(id);
                commit(UPDATE_DIRECTORY, directory);
                commit(SET_CURRENT_DIRECTORY_ID, directory.id);
                commit(SET_PARENT_DIRECTORY_ID, directory.parent)
                commit(SET_LOADING, false);
            } else {
                commit(SET_CURRENT_DIRECTORY_ID, id);
                commit(SET_PARENT_DIRECTORY_ID, state.directoryById[id].parent)
            }
        },
    },
    mutations: {
        [SET_LOADING] (state, loading: boolean) {
            state.loading = loading;
        },
        [SET_CURRENT_DIRECTORY_ID] (state, directoryId) {
            state.currentId = directoryId;
        },
        [SET_PARENT_DIRECTORY_ID] (state, parentId) {
            state.parentId = parentId
        },
        [UPDATE_DIRECTORY] (state, directory) {
            state.directoryById[directory.id] = directory;
        }
    },
};

export default FileBrowserStore;
