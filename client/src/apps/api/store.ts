export const DO_SOMETHING = 'DO_SOMETHING';

const APIStoreModule = {
  namespaced: true,
  state () {
    return {
      asd: {},
    };
  },
  getters: {
    me: (state: any) => state.asd,
  },
  actions: {
    init: async function () {
        // asd
    },
  },
  mutations: {
    [DO_SOMETHING] (state: any, data: any) {
      state.asd = data;
    },
  },
};

export default APIStoreModule;
