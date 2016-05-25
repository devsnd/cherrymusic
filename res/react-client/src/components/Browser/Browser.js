import React from 'react';

import {
  Button,
  Panel,
  ListGroup,
  ListGroupItem,
  Table,
  Label,
  Breadcrumb,
  BreadcrumbItem
} from 'react-bootstrap';

import {LoadingStates} from 'redux/modules/CherryMusicApi';
import TrackListItem from 'components/TrackListItem/TrackListItem';
import SpinnerImage from 'static/img/cherrymusic_loader.gif';
import classes from './Browser.scss';
import folderImage from 'static/img/folder.png';

export class Browser extends React.Component {
  props: Props;

  constructor (props) {
    super(props);
    this.state = {};
    this.selectAll = (trackIds) => {
      for (const trackId of trackIds) {
        this.props.selectTrack(trackId);
      }
    }
  }

  render () {
    const {collections, tracks, entities, state, path} = this.props.fileBrowser;
    const {loadDirectory, selectTrack} = this.props;

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
                header={
                  <span>
                    {collection.label}
                    <img style={{float: 'left', paddingRight: 10}} src={folderImage} />
                  </span>
                }
              >
                {collection.path}
              </ListGroupItem>
            );
          })}
        </ListGroup>
        }

        {!!tracks.length && <div>
            <Button onClick={() => {this.selectAll(tracks)}}>
              Add all to playlist
            </Button>
            <table className="table table-hover">
              <tbody>
                {tracks.map((trackId) => {
                  const track = entities.track[trackId];
                  return (
                    <tr key={trackId}>
                      <td>
                        <TrackListItem
                          track={track}
                          onClick={() => {selectTrack(trackId)}}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        }
      </div>
    )
  }
}

export default Browser;

