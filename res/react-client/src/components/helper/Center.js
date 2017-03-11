import React, {PropTypes} from 'react';

export class Center extends React.Component {
  static propTypes = {
    children: PropTypes.any,
    style: PropTypes.object,
  };

  render () {
    const style = this.props.style || {};
    return (
      <div style={{textAlign: 'center', ...style}}>
        <div>
          {this.props.children}
        </div>
      </div>
    );
  }
}

export default Center;
