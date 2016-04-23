import React from 'react';
import {LoadingStates} from 'redux/modules/CherryMusicApi';
import {MessageOfTheDay} from 'components/MessageOfTheDay/MessageOfTheDay';
import {
  Panel,
  ListGroup,
  ListGroupItem,
  Table,
  Label,
  Breadcrumb,
  BreadcrumbItem
} from 'react-bootstrap';
import SpinnerImage from 'static/img/cherrymusic_loader.gif';
import classes from './Browser.scss';

export class Browser extends React.Component {
  props: Props;

  constructor (props) {
    super(props);
    this.state = {};
  }

  render () {
    const {collections, tracks, entities, state, path} = this.props.fileBrowser;
    const {loadDirectory, selectTrack} = this.props;

    if (state === LoadingStates.idle) {
      return <MessageOfTheDay />;
    }

    if (state === LoadingStates.loading) {
      return (
        <img src={SpinnerImage} style={{
          left: '50%',
          marginLeft: '-40px',
          position: 'relative'
        }}/>
      );
    }

    // build breadcrumbs
    const breadCrumbs = [
      {label: 'Basedir', path: ''}
    ];
    if (path) {
      const splitPaths = path.split('/');
      let fullPath = null;
      for (let i=0; i < splitPaths.length; i++){
        const label = splitPaths[i];
        let fullPathToPart;
        if (i === 0) {
          fullPath = splitPaths[i];
        } else {
          fullPath = fullPath + '/' + splitPaths[i];
        }
        breadCrumbs.push({label: label, path: fullPath});
      }
    }

    return (
      <div>
        <Breadcrumb>
          {breadCrumbs.map((bc) => {
            return (
              <Breadcrumb.Item
                onClick={() => loadDirectory(bc.path)}
                key={bc.path}
              >
                {bc.label}
              </Breadcrumb.Item>
            );
          })}
        </Breadcrumb>
        {!!collections.length &&
        <ListGroup>
          {collections.map((collectionId) => {
            const collection = entities.collection[collectionId];
            return (
              <ListGroupItem
                key={collection.path}
                onClick={() => {loadDirectory(collection.path)}}
                header={collection.label}
              >
                {collection.path}
              </ListGroupItem>
            );
          })}
        </ListGroup>
        }

        {!!tracks.length &&
          <Table hover>
            <thead>
              <tr>
                <th>Artist</th>
                <th>Trackname</th>
              </tr>
            </thead>
            <tbody>
              {tracks.map((trackId) => {
                const track = entities.track[trackId];
                return (
                  <tr key={track.path} onClick={() => {selectTrack(trackId)}}>
                    <td>{track.label}</td>
                    <td>{track.path}</td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        }
      </div>
    )
  }
}

export default Browser;

