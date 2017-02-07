import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  Grid,
  Col,
  Row,
  Glyphicon,
  Input,
  Button,
  Navbar,
  Nav,
  NavItem,
  NavDropdown,
  MenuItem,
} from 'react-bootstrap';

import AudioPlayer from 'components/AudioPlayer/AudioPlayer';
import Browser from 'components/Browser/Browser';
import TabbedPlaylists from 'components/TabbedPlaylists/TabbedPlaylists';
import PlaylistBrowser from 'components/PlaylistBrowser/PlaylistBrowser';
import {MessageOfTheDay} from 'components/MessageOfTheDay/MessageOfTheDay';

import {
  loadDirectory,
  search,
  actionPlaylistListRequested,
  PlaylistSortModes,
} from 'redux/modules/CherryMusicApi';
import { setBrowserView, setPlaylistView, ViewStates } from 'redux/modules/UI';
import { loginStates } from 'redux/modules/Auth';
import { addTrackIdToOpenPlaylist } from 'redux/modules/PlaylistManager';

import { push } from 'react-router-redux';
import { bindActionCreators } from 'redux';

import navbarBrandLogoPng from 'static/img/favicon32-black.png';
import cssClasses from './MainView.scss';

export class MainView extends React.Component {
  static propTypes = {
    loadDirectory: PropTypes.func.isRequired,
    dispatch: PropTypes.func.isRequired,
    loginState: PropTypes.string.isRequired,
  };

  static contextTypes = {
    store: PropTypes.object,
  };

  constructor (props) {
    super(props);
    this.state = {
      viewPortHeight: 500,
      navBarExpanded: false,
    }; // initial UI state
    this.loadDirectory = bindActionCreators(this.props.loadDirectory, this.props.dispatch);
    this.setBrowserView = bindActionCreators(this.props.setBrowserView, this.props.dispatch);
    this.setPlaylistView = bindActionCreators(this.props.setPlaylistView, this.props.dispatch);
    this.search = bindActionCreators(this.props.search, this.props.dispatch);
    this.addTrackIdToOpenPlaylist = bindActionCreators(this.props.addTrackIdToOpenPlaylist, this.props.dispatch);

    this.uiBrowseFiles = () => {
      this.setBrowserView();
      this.loadDirectory('');
      this.setState({navBarExpanded: false});
    };
    this.uiLoadPlaylists = () => {
      this.setPlaylistView();
      this.props.dispatch(actionPlaylistListRequested(PlaylistSortModes.default, ''));
      this.setState({navBarExpanded: false});
    };
    this.updateViewPortSize = this.updateViewPortSize.bind(this);
    this.handleNavBarSearch = this.handleNavBarSearch.bind(this)
    this.handleNavBarToggle = this.handleNavBarToggle.bind(this)
  }

  componentDidMount () {
    // make sure that we are logged in:
    if (this.props.loginState !== loginStates.logInSuccess) {
      this.props.dispatch(push('/login'));
    }

    // hitting enter in the search bar starts a search:
    this.refs.navBarSearchInput.refs.input.addEventListener('keydown', (evt) => {
      if (evt.keyCode == 13) {
        this.handleNavBarSearch();
      }
    });

    window.addEventListener('resize', this.updateViewPortSize);
    this.updateViewPortSize();
  }

  componentWillUnmount () {
    window.removeEventListener('resize', this.updateViewPortSize);
  }

  updateViewPortSize () {
    this.setState({viewPortHeight: window.innerHeight });
  }

  handleNavBarToggle () {
    this.setState({navBarExpanded: !this.state.navBarExpanded});
  }

  handleNavBarSearch () {
    this.setBrowserView();
    this.search(this.refs.navBarSearchInput.refs.input.value);
  }

  render () {
    const navBarHeight = 50;
    const playerHeight = 64;
    const {show } = this.props;

    const SearchBar = (
      <Input
        style={{width: '140px', display: 'inline-table'}}
        groupClassName={cssClasses.fixReactBootstrapInput}
        type="text"
        ref="navBarSearchInput"
        buttonAfter={
          <Button onClick={this.handleNavBarSearch}>Search</Button>
        }
      />
    );

    return (
      <div>
        <Navbar
          fluid
          onToggle={this.handleNavBarToggle}
          expanded={this.state.navBarExpanded}>
          <Navbar.Header>
            <Navbar.Brand>
              <a
                href="#"
                className={cssClasses.navbarBrandLogo}
                style={{backgroundImage: 'url("' + navbarBrandLogoPng + '")' }}
              >
                <span className="hidden-xs">Cherry&nbsp;&nbsp;Music</span>
              </a>
            </Navbar.Brand>
            {/* add searchbar in header on mobile */}
            <Navbar.Brand>
              <span className="visible-xs" style={{padding: 9}}>
                {SearchBar}
              </span>
            </Navbar.Brand>
            <Navbar.Toggle />
          </Navbar.Header>
          <Navbar.Collapse>
            <Nav>
              <NavItem
                eventKey={1}
                href="#"
                className="navItemSearchHack hidden-xs"
                style={{width: '210px' /* workaround for chrome rendering the searchbar with 100% width */ }}
              >
                  {SearchBar}
              </NavItem>
              <NavItem eventKey={2} href="#" onClick={this.uiBrowseFiles}>Browse files</NavItem>
              <NavItem eventKey={2} href="#" onClick={this.uiLoadPlaylists}>Load Playlist</NavItem>
              <NavDropdown eventKey={3} title={<Glyphicon glyph="wrench" />} id="basic-nav-dropdown">
                <MenuItem eventKey={3.1}>Options</MenuItem>
                <MenuItem eventKey={3.2}>Admin</MenuItem>
                <MenuItem divider />
                <MenuItem eventKey={3.3}>Logout</MenuItem>
              </NavDropdown>
            </Nav>
          </Navbar.Collapse>
        </Navbar>
        <Grid fluid>
          <Row className="show-grid">
            <Col sm={6}>
              {show === ViewStates.motd &&
                <MessageOfTheDay />
              }
              {show === ViewStates.browser &&
                <Browser
                  fileBrowser={this.props.fileBrowser}
                  loadDirectory={this.loadDirectory}
                  selectTrack={this.addTrackIdToOpenPlaylist}
                  height={
                    /* navbar height (51+20 pad) player height (70) */
                    this.state.viewPortHeight - 71 - 70
                  }
                />
              }
              {show === ViewStates.playlists &&
                <PlaylistBrowser
                  height={
                    /* navbar height (51+20 pad) player height (70) */
                    this.state.viewPortHeight - 71 - 70
                  }
                />
              }
            </Col>
            {/* move the playlists up into the navbar area */}
            {/* style={{top: '-60px'}} */}
            <Col sm={6}>
              <TabbedPlaylists
                 /* lift the tabbed playlists over the file broser, so the
                 browser animation is below the tabbed playlist
                  */
                style={{zIndex: 40}}
                height={
                  /* navbar height (51+20 pad) player height (70) */
                  this.state.viewPortHeight - 71 - 70
                }
                selectTrack={this.props.playPlaylistTrackNr}
              />
            </Col>
          </Row>
        </Grid>
        <AudioPlayer />
      </div>
    );
  }
}

// connect the view to the application state and reducer actions
export default connect(
  (state, dispatch) => {
    return {
      // internalPropName: state.someGlobalApplicationState,
      loginState: state.auth.loginState,
      fileBrowser: state.api,
      show: state.ui.viewState,
    };
  },
  (dispatch) => {
    return {
      dispatch: dispatch,
      loadDirectory: loadDirectory,
      setBrowserView: setBrowserView,
      setPlaylistView: setPlaylistView,
      search: search,
      addTrackIdToOpenPlaylist: addTrackIdToOpenPlaylist,
    };
  }
)(MainView);
