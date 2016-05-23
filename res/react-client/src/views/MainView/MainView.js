import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import { Grid, Col, Row, Glyphicon, Input, Button, Navbar, Nav, NavItem, NavDropdown, MenuItem } from 'react-bootstrap';

import AudioPlayer from 'components/AudioPlayer/AudioPlayer';
import Browser from 'components/Browser/Browser';
import TabbedPlaylists from 'components/TabbedPlaylists/TabbedPlaylists';

import { loadDirectory, search } from 'redux/modules/CherryMusicApi';
import { loginStates } from 'redux/modules/Auth';
import { addTrackIdToOpenPlaylist } from 'redux/modules/Playlist';

import { push } from 'react-router-redux';
import { bindActionCreators } from 'redux';

import navbarBrandLogoPng from 'static/img/favicon32-black.png';
import cssClasses from './MainView.scss';

export class MainView extends React.Component {
  static propTypes = {
    loadDirectory: PropTypes.func.isRequired,
    loginState: PropTypes.string.isRequired,
  };

  static contextTypes = {
    store: PropTypes.object
  };

  constructor (props) {
    super(props);
    this.state = {}; // initial UI state
    this.loadDirectory = bindActionCreators(this.props.loadDirectory, this.props.dispatch);
    this.search = bindActionCreators(this.props.search, this.props.dispatch);
    this.addTrackIdToOpenPlaylist = bindActionCreators(this.props.addTrackIdToOpenPlaylist, this.props.dispatch);
  }

  componentDidMount () {
    // make sure that we are logged in:
    if (this.props.loginState !== loginStates.logInSuccess){
      this.props.dispatch(push('/login'));
    }

    // hitting enter in the search bar starts a search:
    this.refs.navBarSearchInput.refs.input.addEventListener("keydown", (evt) => {
      if (evt.keyCode == 13) {
        this.handleNavBarSearch();
      }
    })
  }

  handleNavBarSearch () {
    this.search(this.refs.navBarSearchInput.refs.input.value);
  }

  render () {
    const navBarHeight = 50;
    const playerHeight = 64;
    return (
      <div>
        <Navbar>
          <Nav>
            <Navbar.Brand>
              <a
                href="#"
                className={cssClasses.navbarBrandLogo}
                style={{backgroundImage: 'url("' + navbarBrandLogoPng + '")'}}
              >
                Cherry&nbsp;&nbsp;Music
              </a>
            </Navbar.Brand>
            <NavItem eventKey={1} href="#" className="navItemSearchHack" >
                <Input
                  style={{width: '140px'}}
                  type="text"
                  ref="navBarSearchInput"
                  buttonAfter={
                    <Button onClick={this.handleNavBarSearch.bind(this)}>Search</Button>
                  }
                />
            </NavItem>
            <NavItem eventKey={2} href="#" onClick={() => {this.loadDirectory('')}}>Browse files</NavItem>
            <NavItem eventKey={2} href="#">Load Playlist</NavItem>
            <NavDropdown eventKey={3} title={<Glyphicon glyph="wrench" />} id="basic-nav-dropdown">
              <MenuItem eventKey={3.1}>Options</MenuItem>
              <MenuItem eventKey={3.2}>Admin</MenuItem>
              <MenuItem divider />
              <MenuItem eventKey={3.3}>Logout</MenuItem>
            </NavDropdown>
          </Nav>
        </Navbar>
        <Grid>
          <Row className="show-grid">
            <Col md={6}>
              <Browser
                fileBrowser={this.props.fileBrowser}
                loadDirectory={this.loadDirectory}
                selectTrack={this.addTrackIdToOpenPlaylist}
              />
            </Col>
            {/* move the playlists up into the navbar area */}
            {/* style={{top: '-60px'}} */}
            <Col md={6}>
              <TabbedPlaylists
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
    };
  },
  (dispatch) => {
    return {
      dispatch: dispatch,
      loadDirectory: loadDirectory,
      search: search,
      addTrackIdToOpenPlaylist: addTrackIdToOpenPlaylist,
    };
  }
)(MainView);
