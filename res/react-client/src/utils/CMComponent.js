import React from 'react';

class CMComponent extends React.Component {
  render () {
    try {
      return this.safeRender();
    } catch (exc) {
      console.log(exc);
      return (
        <div style={{backgroundColor: '#ffeeee', fontFamily: 'mono-space'}}>
          {'' + exc}<br />
          <h3>Props:</h3><br />
          <div style={{overflowY: 'scroll', height: 200}}>
            {JSON.stringify(this.props)}<br />
          </div>
          <h3>State:</h3><br />
          {JSON.stringify(this.state)}<br />
          <code style={{fontSize: 'small'}}>
            {exc.stack}
          </code>
        </div>
      );
    }
  }
}

export default CMComponent;
