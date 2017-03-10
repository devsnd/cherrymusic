import Username from 'components/Username/Username';
import Age from 'components/Age/Age';
import {ListGroupItem, Label, Button} from 'react-bootstrap';
import React, {PropTypes} from 'react';

export class PlaylistBrowserItem extends React.Component {
  static propTypes = {
    playlist: PropTypes.object.isRequired,
    delete: PropTypes.func,
    setPublic: PropTypes.func,
    open: PropTypes.func,
  };

  constructor (props) {
    super(props);
    this.handleListItemClick = (evt) => {
      // this handler is fired even when we hit children of the listItem,
      // but we only want to trigger the handler if the listitem is clicked
      // directly
      if (evt.target.dataset.type === 'parentListItem') {
        this.props.open(evt);
      }
    };

    this.setPublicEnabled = (evt) => {
      evt.stopPropagation();
      this.props.setPublic(true);
    };
    this.setPublicDisabled = (evt) => {
      evt.stopPropagation();
      this.props.setPublic(false);
    };
  }

  render () {
    const playlist = this.props.playlist;
    const inputChecked = playlist.public ? {checked: true } : {};
    return (
      <ListGroupItem
        onClickCapture={this.handleListItemClick}
        data-type="parentListItem"
        key={playlist.plid}
      >
        {playlist.title}
        {playlist.owner && <span>
          <Button
            bsStyle="danger"
            bsSize="xsmall"
            style={{float: 'right', marginLeft: 10 }}
            onClick={this.props.delete}
          >
            &times;
          </Button>
          <Label
            bsStyle={playlist.public ? 'success' : 'default'}
            style={{float: 'right' }}
            onClick={playlist.public ? this.setPublicDisabled : this.setPublicEnabled}
          >
              public&nbsp;<input
                type="checkbox"
                {...inputChecked}
            />
          </Label>
        </span>}
        <span style={{float: 'right' }}>
          <Age seconds={playlist.age} />
        </span>
        <Username name={playlist.username} />
      </ListGroupItem>
    );
  }
}

export default PlaylistBrowserItem;
