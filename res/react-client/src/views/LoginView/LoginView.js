import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import { login, loginStates } from 'redux/modules/Auth';
import { Input, Button, Well, Alert, Grid, Row, Col } from 'react-bootstrap';
import { errorMessage } from 'redux/modules/Messages';
import classes from './LoginView.scss';
import CherryMusicLogoImage from '../../static/img/cherrymusic_logo_big.png';

export class LoginView extends React.Component {
  static propTypes = {
    errorMessage: PropTypes.func.isRequired,
    login: PropTypes.func.isRequired,
    loginState: PropTypes.string.isRequired,
  };

  static contextTypes = {
    store: PropTypes.object,
  };

  constructor (props) {
    super(props);
    this.state = {}; // initial UI state
    this.handleLogin = ::this.handleLogin;
  }

  componentDidMount () {
    this.refs.username.refs.input.focus();
    // submit form when pressing enter:
    this.refs.loginform.addEventListener('keydown', (evt) => {
      if (evt.keyCode === 13) {
        this.handleLogin();
      }
    });
    //console.log('HACKED AUTOLOGIN!!!!');
    //this.props.login('u', 'p');
  }

  handleLogin () {
    const username = this.refs.username.refs.input.value;
    const password = this.refs.password.refs.input.value;
    this.props.login(username, password);
  }

  render () {
    const { loginState } = this.props;
    return (
      <div>
        <br />
        <Grid>
          <Row>
            <Col sm={4} smOffset={4}>
              <img className={classes.loginLogo}
                src={CherryMusicLogoImage}
                alt='CherryMusic is very nice.'
              />
              <h3 style={{textAlign: 'center'}}>Cherry Music</h3>
              <Well className={loginState === loginStates.logInFailed && 'shake-animation'}>
                <form ref="loginform">
                  <Input
                    type="text"
                    ref="username"
                    label="Username"
                    placeholder="Username"
                    disabled={loginState === loginStates.loggingIn} />
                  <Input
                    type="password"
                    ref="password"
                    label="Password"
                    placeholder="Password"
                    disabled={loginState === loginStates.loggingIn} />
                  <Button
                    onClick={this.handleLogin}
                    bsStyle="primary"
                  >
                    Login
                  </Button>
                </form>
                <br />
                {loginState === loginStates.logInFailed &&
                  <Alert bsStyle="warning">Login failed. Wrong username or password.</Alert>
                }
                {loginState === loginStates.logInError &&
                  <Alert bsStyle="danger">Error connecting to server.</Alert>
                }
                <a className="fomori" target="_blank" href="http://www.fomori.org">
                  visit fomori.org
                </a>
              </Well>
            </Col>
          </Row>
        </Grid>
      </div>
    );
  }
}

// connect the view to the application state and reducer actions
export default connect(
  (state) => {
    return {
      loginState: state.auth.loginState,
    };
  }, {
    login: login,
    errorMessage: errorMessage,
  }
)(LoginView);
