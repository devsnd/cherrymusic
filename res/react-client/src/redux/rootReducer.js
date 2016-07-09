import { combineReducers } from 'redux';
import { routerReducer as router } from 'react-router-redux';
import CherryMusicApi from './modules/CherryMusicApi';
import Playlist from './modules/Playlist';
import Auth from './modules/Auth';
import UI from './modules/UI';
import Player from './modules/Player';

export default combineReducers({
  router,
  api: CherryMusicApi,
  ui: UI,
  playlist: Playlist,
  auth: Auth,
  player: Player
});
