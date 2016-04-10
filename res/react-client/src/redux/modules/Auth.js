import {legacyAPICall, postForm} from 'utils/legacyApi';
import {API_ENDPOINT_LOGOUT, API_ENDPOINT_LOGIN} from 'constants';
import { push } from 'react-router-redux';

export const LOGGING_IN = 'redux/cherrymusic/LOGGING_IN';
export const LOG_IN_SUCCESS = 'redux/cherrymusic/LOG_IN_SUCCESS';
export const LOG_IN_FAILED = 'redux/cherrymusic/LOG_IN_FAILED';
export const LOGGING_OUT = 'redux/cherrymusic/LOGGING_OUT';
export const LOGGED_OUT= 'redux/cherrymusic/LOGGED_OUT';

export const loginStates = {
  loggingIn: 'loggingIn',
  logInSuccess: 'logInSuccess',
  logInError: 'logInError',
  logInFailed: 'logInFailed',
  loggingOut: 'loggingOut',
  logOutSuccess: 'logOutSuccess',
};

function actionLoggingIn () { return {type: LOGGING_IN, payload: {}}; }
function actionLogInSuccess (username, authtoken) { return {type: LOG_IN_SUCCESS, payload: {username: username, authtoken: authtoken}}; }
function actionLogInFailed (username) { return {type: LOG_IN_FAILED, payload: {}}; }
function actionLoggingOut () { return {type: LOGGING_OUT, payload: {}}; }
function actionLoggedOut () { return {type: LOGGED_OUT, payload: {}}; }

export function login (username, password) {
  return (dispatch, getState) => {
    dispatch(actionLoggingIn());
    legacyAPICall(
      API_ENDPOINT_LOGIN,
      {
        'username': username,
        'password': password
      }
    ).then(
      (data) => {
        console.log(data);
        dispatch(actionLogInSuccess(username, data['authtoken']));
        // http://stackoverflow.com/a/34863577/1191373
        dispatch(push('/main'));
      },
      (error) => {
        console.log(error);
        dispatch(actionLogInFailed());
      }
    );
  }
}

export function logout () {
  return (dispatch, getState) => {
    dispatch(actionLoggingOut());
    legacyAPICall(API_ENDPOINT_LOGOUT).then(
      (data) => { dispatch(actionLogOutSuccess()); },
      (error) => { alert('error logging out!') }
    )
  }

}

export function setPassword (oldPassword, newPassword) {
  return (dispatch, getState) => {
    legacyAPICall(
      API_ENDPOINT_CHANGEPASSWORD,
      {
        "oldpassword": oldPassword,
        "newpassword": newPassword
      }
    ).then(
      (data) => { alert('Password changed successfully!')},
      (error) => { alert('Error changing password!'); console.log(error); }
    )
  }
}

export const initialState = {
  loginState: loginStates.logOutSuccess,
  user: null,
  userOptions: {}
};

const ACTION_HANDLERS = {
  [LOGGING_IN]: (state, action) => {
    return {
      ...state,
      loginState: loginStates.loggingIn,
    }
  },
  [LOG_IN_SUCCESS]: (state, action) => {
    return {
      ...state,
      loginState: loginStates.logInSuccess,
      user: {
        username: action.payload.username
      },
    }
  },
  [LOG_IN_FAILED]: (state, action) => {
    return {
      ...state,
      loginState: loginStates.logInFailed,
      user: null,
    }
  }
  // SOME_ACTION: (state, action) => {
  //   return state;
  // }
};

export default function (state = initialState, action) {
  const handler = ACTION_HANDLERS[action.type];
  return handler ? handler(state, action) : state;
}

