import React, {PropTypes } from 'react';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import classes from './FadeIn.scss';

export default class FadeIn extends React.Component {
  static propTypes = {
    speed: PropTypes.string,
    children: React.PropTypes.oneOfType([
      React.PropTypes.arrayOf(React.PropTypes.node),
      React.PropTypes.node,
    ]),
  };

  render () {
    let transitionNames = {
      enter: classes.fadeInEnter,
      enterActive: classes.fadeInEnterActive,
      appear: classes.fadeInEnter,
      appearActive: classes.fadeInEnterActive,
      leave: classes.fadeInLeave,
      leaveActive: classes.fadeInLeaveActive,
    };
    return (
      <ReactCSSTransitionGroup
        transitionName={transitionNames}
        transitionAppear
        transitionAppearTimeout={200}
        transitionEnterTimeout={200}
        transitionLeaveTimeout={200}
      >
        {this.props.children}
      </ReactCSSTransitionGroup>
    );
  }
}
