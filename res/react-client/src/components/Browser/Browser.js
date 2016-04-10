import React from 'react';
import {LoadingStates} from 'redux/modules/CherryMusicApi';
import {MessageOfTheDay} from 'components/MessageOfTheDay/MessageOfTheDay';
import {Panel, ListGroup, ListGroupItem, Table, Label} from 'react-bootstrap';
import SpinnerImage from 'static/img/cherrymusic_loader.gif';
import classes from './Browser.scss';

export class Browser extends React.Component {
  props: Props;

  constructor (props) {
    super(props);
    this.state = {};
  }

  render () {
    const {collections, tracks, state, path} = this.props.fileBrowser;
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
      <span key={'rootBreadcrumb'} onClick={() => loadDirectory('')}>Basedir</span>
    ];
    if (path) {
      const splitPaths = path.split('/');
      let assembledPaths = null;
      for (let i=0; i < splitPaths.length; i++){
        breadCrumbs.push(<span> / </span>);
        const label = splitPaths[i];
        let fullPathToPart;
        if (i === 0) {
          assembledPaths = splitPaths[i];
        } else {
          assembledPaths = assembledPaths + '/' + splitPaths[i];
        }
        fullPathToPart = assembledPaths;
        breadCrumbs.push(<span key={fullPathToPart} onClick={() => loadDirectory(fullPathToPart)}>{label}</span>);
      }
    }

    return (
      <div>
        {breadCrumbs}
        <br/>
        <br/>
        {!!collections.length &&
        <ListGroup>
          {collections.map((collection) => {
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
              {tracks.map((track) => {
                return (
                  <tr key={track.path} onClick={() => {selectTrack(track)}}>
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

