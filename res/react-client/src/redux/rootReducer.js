import { combineReducers } from 'redux';
import { routerReducer as router } from 'react-router-redux';
import CherryMusicApi from './modules/CherryMusicApi';
import Playlist from './modules/Playlist';
import Auth from './modules/Auth';
import UI from './modules/UI';
import Player from './modules/Player';
import BrowserDuck from 'components/Browser/BrowserDuck';

export default combineReducers({
  router,
  api: CherryMusicApi,
  browser: BrowserDuck,
  ui: UI,
  playlist: Playlist,
  auth: Auth,
  player: Player
});
