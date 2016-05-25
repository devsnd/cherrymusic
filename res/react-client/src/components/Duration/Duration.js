import React, {PropTypes} from 'react';


class Duration extends React.Component {
  static propTypes = {
    seconds: PropTypes.number.isRequired,
  };

  constructor(props) {
    super(props);
  }

  render() {
    const {seconds} = this.props;
    const hrs = Math.floor(seconds / 3600);
    let mins = Math.floor(seconds / 60) % 60;
    let secs = Math.floor(seconds) % 60;
    // always show leading zero in seconds
    if (secs < 10) {
      secs = '0' + secs;
    }
    // only show leading zero in minutes if there are any hours
    if (hrs > 0 && mins < 10) {
      mins = '0' + mins;
    }
    return (
      <span {...this.props}>{hrs !== 0 && <span>{hrs}:</span>}{mins}:{secs}</span>
    );
  }
}

export default Duration;
