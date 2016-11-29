import { applyMiddleware, compose, createStore } from 'redux';
import thunk from 'redux-thunk';
import rootReducer from './rootReducer';
import { routerMiddleware } from 'react-router-redux';
import createSagaMiddleware from 'redux-saga';
import {MetaDataWatcher } from 'redux/sagas/MetaDataLoaderSaga';
import {PlaylistLoaderSaga } from 'redux/sagas/PlaylistLoaderSaga';

export default function configureStore (initialState = {}, history) {
  // Compose final middleware and use devtools in debug environment
  const sagaMiddleware = createSagaMiddleware();

  let middleware = applyMiddleware(
    thunk,
    routerMiddleware(history),
    sagaMiddleware
  );

  if (__DEBUG__) {
    const devTools = window.devToolsExtension
      ? window.devToolsExtension()
      : require('containers/DevTools').default.instrument();
    middleware = compose(middleware, devTools);
  }

  // Create final store and subscribe router in debug env ie. for devtools
  const store = middleware(createStore)(rootReducer, initialState);

  // activate all sagas:
  sagaMiddleware.run(MetaDataWatcher);
  sagaMiddleware.run(PlaylistLoaderSaga);

  if (module.hot) {
    module.hot.accept('./rootReducer', () => {
      const nextRootReducer = require('./rootReducer').default;

      store.replaceReducer(nextRootReducer);
    });
  }
  return store;
}
