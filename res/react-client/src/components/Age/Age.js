import React, {PropTypes } from 'react';


class Age extends React.Component {
  static propTypes = {
    seconds: PropTypes.number.isRequired,
  };

  constructor (props) {
    super(props);
  }

  secondsPerMinute = 60;
  secondsPerHour = this.secondsPerMinute * 60;
  secondsPerDay = this.secondsPerHour * 24;
  secondsPerMonth = this.secondsPerDay * 30;
  secondsPerYear = this.secondsPerDay * 365;

  units = [
    [this.secondsPerMinute, 'minute', 'minutes' ],
    [this.secondsPerHour, 'hour', 'hours' ],
    [this.secondsPerDay, 'day', 'days' ],
    [this.secondsPerMonth, 'month', 'months' ],
    [this.secondsPerYear, 'year', 'years' ],
  ];

  render () {
    const {seconds } = this.props;
    if (typeof seconds === 'undefined') {
      return (<span>error</span>);
    }

    if (Math.abs(seconds) < 60) {
      return <span>just now</span>;
    }

    let currentUnit = this.units[0];
    for (const unit of this.units) {
      if (seconds > unit[0]) {
        currentUnit = unit;
      } else {
        break;
      }
    }
    const count = Math.floor(seconds / currentUnit[0]);

    if (count > 1) {
      return <span>{count} {currentUnit[2]} ago</span>;
    } else if (count == 1) {
      return <span>1 {currentUnit[1]} ago</span>;
    }
    if (count < -1) {
      return <span>in {count} {currentUnit[2]}</span>;
    } else if (count == -1) {
      return <span>in 1 {currentUnit[1]}</span>;
    }
  }
}

export default Age;
