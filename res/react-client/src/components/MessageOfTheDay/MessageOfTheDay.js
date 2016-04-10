import React from 'react';

export class MessageOfTheDay extends React.Component {
  constructor () {
    super();
    this.state = {
      motd: 'Message of the day'
    };
  }

  componentDidMount () {
    // request message of the day
  }

  render () {
    return (
      <div>
        {this.state.motd}
      </div>
    )
  }
}

export default MessageOfTheDay;

