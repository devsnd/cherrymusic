// Constants

// export const SOME_ACTION = 'SOME_ACTION';

export const initialState = {};

// Action HANDLERS
const ACTION_HANDLERS = {
  // SOME_ACTION: (state, action) => {
  //   return state;
  // }
};

export default function (state = initialState, action) {
  const handler = ACTION_HANDLERS[action.type];
  return handler ? handler(state, action) : state;
}

