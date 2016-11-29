import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

import {initPlayer, playerStates, seek, pause, resume } from 'redux/modules/Player';
import {playNextTrack, playPreviousTrack } from 'redux/modules/PlaylistManager';

import classes from './AudioPlayer.scss';
import {ProgressBar, Glyphicon, Button, ButtonGroup } from 'react-bootstrap';

export class AudioPlayer extends React.Component {
  constructor (props) {
    super(props);
    this.state = {};
    this.handleProgressBarClick = this.handleProgressBarClick.bind(this);
  }

  componentDidMount () {
    // attach the HTML5 Player to the DOM element of this component
    this.initPlayer = bindActionCreators(this.props.initPlayer, this.props.dispatch);
    this.seek = bindActionCreators(this.props.seek, this.props.dispatch);
    this.pause = bindActionCreators(this.props.pause, this.props.dispatch);
    this.resume = bindActionCreators(this.props.resume, this.props.dispatch);
    this.playPreviousTrack = bindActionCreators(this.props.playPreviousTrack, this.props.dispatch);
    this.playNextTrack = bindActionCreators(this.props.playNextTrack, this.props.dispatch);
    this.initPlayer(this.refs.audioPlayer);
    this.handleProgressBarClick = this.handleProgressBarClick.bind(this);
  }

  handleProgressBarClick (event) {
    let target = event.target;
    if (target.className.indexOf('progress-bar') >= 0) {
      // we hit the progress indicator instead of the complete progress bar:
      target = target.parentNode;  // this should be the .progress class now.
    }
    const progressBarWidth = target.clientWidth;
    const clickX = event.nativeEvent.clientX;
    const percentage = (clickX / progressBarWidth) * 100;
    this.seek(percentage);
  }

  render () {
    const {playerState } = this.props;
    return (
      <div className={classes.CMAudioPlayer} ref="audioPlayer">
        {this.props.playerState === playerStates.uninitialized &&
          <h1>Initializing player...</h1>
        }
        {playerState !== playerStates.uninitialized &&
        <div>
          <div className={classes.buttonContainer}>
            <ButtonGroup>
              <Button onClick={this.playPreviousTrack}><Glyphicon glyph="step-backward" /></Button>
              {playerState === playerStates.playing &&
                <Button onClick={this.pause}><Glyphicon glyph="pause" /></Button>
              }
              {playerState !== playerStates.playing &&
                <Button onClick={this.resume}><Glyphicon glyph="play" /></Button>
              }
              <Button onClick={this.playNextTrack}><Glyphicon glyph="step-forward" /></Button>
            </ButtonGroup>
            <ButtonGroup bsSize="xs">
              {/*
                lets remove the volume controls until somebody complains, maybe nobody uses them?
                <Button><Glyphicon glyph="volume-off"/></Button>
                <Button><Glyphicon glyph="volume-up"/></Button>
              */}
              <Button><Glyphicon glyph="random" /></Button>
              <Button><Glyphicon glyph="retweet" /></Button>
            </ButtonGroup>
          </div>
          <ProgressBar
            ref="progressBar"
            now={this.props.percentage}
            label={this.props.trackLabel}
            striped={playerState === playerStates.startingPlay}
            onClick={this.handleProgressBarClick}
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
      seek: seek,
      pause: pause,
      resume: resume,
      playNextTrack: playNextTrack,
      playPreviousTrack: playPreviousTrack,
      initPlayer: initPlayer,
    };
  }
)(AudioPlayer);
