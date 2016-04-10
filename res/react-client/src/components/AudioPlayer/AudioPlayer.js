import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux'

import {initPlayer, playerStates} from 'redux/modules/Player'

import classes from './AudioPlayer.scss';
import {ProgressBar, Glyphicon, Button, ButtonGroup} from 'react-bootstrap';

export class AudioPlayer extends React.Component {
  constructor (props) {
    super(props);
    this.state = {};
  }

  componentDidMount () {
    // attach the HTML5 Player to the DOM element of this component
    this.initPlayer = bindActionCreators(this.props.initPlayer, this.props.dispatch);
    this.initPlayer(this.refs.audioPlayer);
  }

  render () {
    return (
      <div className={classes.CMAudioPlayer} ref="audioPlayer">
        {this.props.playerState === playerStates.uninitialized &&
          <h1>Initializing player...</h1>
        }
        {this.props.playerState !== playerStates.uninitialized &&
        <div>
          <div className={classes.buttonContainer}>
            <ButtonGroup>
              <Button><Glyphicon glyph="step-backward"/></Button>
              <Button><Glyphicon glyph="play"/></Button>
              <Button><Glyphicon glyph="step-forward"/></Button>
              <Button><Glyphicon glyph="stop"/></Button>
            </ButtonGroup>
            <ButtonGroup bsSize="xs">
              <Button><Glyphicon glyph="volume-off"/></Button>
              <Button><Glyphicon glyph="volume-up"/></Button>
              <Button><Glyphicon glyph="random"/></Button>
              <Button><Glyphicon glyph="retweet"/></Button>
            </ButtonGroup>
          </div>
          <ProgressBar
            now={this.props.percentage}
            label={this.props.trackLabel}
          />
        </div>
        }
      </div>
    );
  }
}

export default connect(
  (state, dispatch) => {
    return {
      playerState: state.player.state,
      percentage: state.player.percentage,
      trackLabel: state.player.trackLabel,
    };
  },
  (dispatch) => {
    return {
      dispatch: dispatch,
      initPlayer: initPlayer
    };
  }
)(AudioPlayer);
