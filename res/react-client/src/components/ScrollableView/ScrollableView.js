import React, {PropTypes } from 'react';

export class ScrollableView extends React.Component {
  static propTypes = {
    children: PropTypes.any,
    height: PropTypes.number,
    style: PropTypes.object,
  };

  render () {
    const otherProps = {...this.props };
    const style = this.props.style || {};
    delete otherProps.style;
    delete otherProps.height;
    delete otherProps.children;
    const height = typeof this.props.height === 'undefined' ? '200px' : this.props.height + 'px';
    return (
      <div
        {...otherProps}
        style={{'overflowY': 'scroll', height: height, ...style}}
      >
        {this.props.children}
      </div>
    );
  }
}

export default ScrollableView;
