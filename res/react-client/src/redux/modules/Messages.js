import {createSelector } from 'reselect';
// Constants
export const ADD_MESSAGE = 'abend/redux/impersonate/ADD_MESSAGE';
export const REMOVE_MESSAGES = 'abend/redux/impersonate/REMOVE_MESSAGES';
const REMOVE_MESSAGE_INTERVAL_MILLIS = 8000;

export const Level = {
  Error: 'Error',
  Warning: 'Warning',
  Info: 'Info',
  Success: 'Success',
};

export const errorMessage = (errormessage) => {
  return (dispatch, getState) => {
    _addMessage({level: Level.Error, message: errormessage })(dispatch, getState);
  };
};

export const actionErrorMessage = (errormessage) => {
  return actionAddMessage({level: Level.Error, message: errormessage });
};

export const successMessage = (successMessage) => {
  return (dispatch, getState) => {
    _addMessage({level: Level.Success, message: successMessage })(dispatch, getState);
  };
};

export const actionSuccessMessage = (successmessage) => {
  return actionAddMessage({level: Level.Success, message: successmessage });
};

export const actionAddMessage = (message) => {
  return {
    type: ADD_MESSAGE,
    payload: {
      message: {
        level: message.level,
        message: message.message,
        dateCreated: new Date(),
      },
    },
  };
};

const _addMessage = (message) => {
  return (dispatch, getState) => {
    dispatch(actionAddMessage(message));
    // remove old messages just after this one expires:
    window.setTimeout(
        () => { dispatch({type: REMOVE_MESSAGES, payload: {} }); }, REMOVE_MESSAGE_INTERVAL_MILLIS
    );
  };
};

export const initialState = {
  messages: [],
};

const select = (appState) => appState.messages;

export const selectMessages = createSelector(
  select,
  (state) => state.messages
);

let __messageKey = 0;  // unique key per message for easier react rendering

const ACTION_HANDLERS = {
  [ADD_MESSAGE]: (state, action) => {
    return {
      ...state,
      messages: [
        ...state.messages,
        {
          ...action.payload.message,
          key: __messageKey++,
        },
      ],
    };
  },
  [REMOVE_MESSAGES]: (state, action) => {
    const nowMillis = +new Date();
    const newMessages = state.messages.filter((msg) => {
      // keep message if the current time has passed the expiry time of the message
      return nowMillis < +msg.dateCreated + REMOVE_MESSAGE_INTERVAL_MILLIS;
    });
    if (newMessages.length === state.messages.length) {
      // if no message expired, do not update the state to prevent rerendering
      return state;
    }
    return {
      ...state,
      messages: newMessages,
    };
  },
};

export default function (state = initialState, action) {
  const handler = ACTION_HANDLERS[action.type];
  return handler ? handler(state, action) : state;
}
