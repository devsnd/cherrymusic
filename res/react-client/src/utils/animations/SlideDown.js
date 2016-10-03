import React, {PropTypes} from 'react';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import classes from './SlideDown.scss';

export default class SlideDown extends React.Component {
  static propTypes = {
    speed: PropTypes.string,
    children: React.PropTypes.oneOfType([
      React.PropTypes.arrayOf(React.PropTypes.node),
      React.PropTypes.node
    ]),
  };

  render () {
    let transitionNames = {
      enter: classes.slideDownEnter,
      enterActive: classes.slideDownEnterActive,
      appear: classes.slideDownEnter,
      appearActive: classes.slideDownEnterActive,
      leave: classes.slideDownLeave,
      leaveActive: classes.slideDownLeaveActive,
    };
    return (
      <ReactCSSTransitionGroup
        transitionName={transitionNames}
        transitionAppear
        transitionAppearTimeout={500}
        transitionEnterTimeout={500}
        transitionLeaveTimeout={500}
      >
        {this.props.children}
      </ReactCSSTransitionGroup>
    );
  }
}
