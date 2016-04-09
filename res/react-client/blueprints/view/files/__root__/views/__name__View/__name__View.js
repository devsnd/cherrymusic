import React, { PropTypes } from 'react';
import { connect } from 'react-redux';

export class <%= pascalEntityName %>View extends React.Component {
  static propTypes = {
  };

  static contextTypes = {
    store: PropTypes.object
  };

  constructor (props) {
    super(props);
    this.state = {}; // initial UI state
  }

  componentDidMount () {
    // do stuff when the view is first inserted into dom, e.g. request data etc
  }

  render () {
    return (
      <div></div>
    );
  }
}

// connect the view to the application state and reducer actions
export default connect(
  (state) => {
    return {
      internalPropName: state.someGlobalApplicationState,
    };
  }, {
    internalPropName: someImportedFunctionFromAReducer
  }
)(<%= pascalEntityName %>View);
