import React, {PropTypes} from 'react';

import {Badge} from 'react-bootstrap';

class Username extends React.Component {
  static propTypes = {
    name: PropTypes.string.isRequired,
  };

  dec2Hex = (dec) => {
    dec = Math.max(0, Math.min(dec, 255));
    const hexChars = "0123456789ABCDEF";
    return hexChars.charAt(Math.floor(dec / 16)) + hexChars.charAt(dec % 16);
  };

  userNameToColor = (username) => {
    username = username.toUpperCase();
    username += 'AAA';
    var g = ((username[0].charCodeAt(0) - 65) * 255) / 30;
    var b = ((username[1].charCodeAt(0) - 65) * 255) / 30;
    var r = ((username[2].charCodeAt(0) - 65) * 255) / 30;
    return '#'+this.dec2Hex(r)+this.dec2Hex(g)+this.dec2Hex(b);
  };

  constructor(props) {
    super(props);
    this.color = this.userNameToColor(props.name);
  }

  render() {
    return <Badge style={{backgroundColor: this.color}}>{this.props.name}</Badge>;
  }
}

export default Username;
