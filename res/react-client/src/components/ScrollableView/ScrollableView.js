import React, {PropTypes} from 'react';

export class ScrollableView extends React.Component {
  static propTypes = {
    children: PropTypes.any,
    height: PropTypes.number,
  };

  render () {
    const height = typeof this.props.height === 'undefined' ? '200px' : this.props.height + 'px';
    return (
      <div style={{'overflowY': 'scroll', height: height}}>
        {this.props.children}
      </div>
    )
  }
}

export default ScrollableView;
