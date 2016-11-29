import React, {PropTypes } from 'react';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import classes from './MoveIn.scss';

export const Direction = {
  left: 'left',
  right: 'right',
};

export default class MoveIn extends React.Component {
  static propTypes = {
    direction: PropTypes.string,
    children: PropTypes.any,
  };

  render () {
    const direction = this.props.direction || Direction.left;
    let transitionNames = null;
    if (direction === Direction.left) {
      transitionNames = {
        enter: classes.moveInLeftEnter,
        enterActive: classes.moveInLeftEnterActive,
        appear: classes.moveInLeftEnter,
        appearActive: classes.moveInLeftEnterActive,
        leave: classes.moveInLeftLeave,
        leaveActive: classes.moveInLeftLeaveActive,
      };
    } else if (direction === Direction.right) {
      transitionNames = {
        enter: classes.moveInRightEnter,
        enterActive: classes.moveInRightEnterActive,
        appear: classes.moveInRightEnter,
        appearActive: classes.moveInRightEnterActive,
        leave: classes.moveInRightLeave,
        leaveActive: classes.moveInRightLeaveActive,
      };
    } else {
      console.log(`Unknown animation direction ${direction}!`);
    }
    return (
      <ReactCSSTransitionGroup
        transitionName={transitionNames}
        transitionAppear
        transitionAppearTimeout={1100}
        transitionEnterTimeout={1100}
        transitionLeaveTimeout={1100}
      >
        {this.props.children
            /*
            the outer span gets the animation classes, the inner one makes that the child renders normally
            */
            ? <span><span style={{'display': 'inline-block' }}>{this.props.children}</span></span>
            : null
        }
      </ReactCSSTransitionGroup>
    );
  }
}
