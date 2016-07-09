import React from 'react';
import {connect} from 'react-redux';
import {
  selectFileListingViewFormat,
  FileListingViewFormats,
  actionSetFileListingViewFormat,
} from './BrowserDuck';

import {
  Button,
  ButtonGroup,
  Panel,
  ListGroup,
  ListGroupItem,
  Table,
  Label,
  Breadcrumb,
  BreadcrumbItem,
  Thumbnail,
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
    };
    this.setListView = () => {
      this.props.dispatch(actionSetFileListingViewFormat(FileListingViewFormats.List));
    };
    this.setTileView = () => {
      this.props.dispatch(actionSetFileListingViewFormat(FileListingViewFormats.Tile));
    };
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


    const viewFormatList = this.props.viewFormat === FileListingViewFormats.List;
    const viewFormatTile = this.props.viewFormat === FileListingViewFormats.Tile;

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
        <ButtonGroup style={{marginBottom: '10px'}}>
          <Button active={viewFormatList} onClick={this.setListView}>
            List
          </Button>
          <Button active={viewFormatTile} onClick={this.setTileView}>
            Tile
          </Button>
        </ButtonGroup>
        {!!collections.length && <div>

          {viewFormatList &&
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
          {viewFormatTile && <div>
            {collections.map((collectionId) => {
              const collection = entities.collection[collectionId];
              return (
                <Thumbnail
                  onClick={() => {loadDirectory(collection.path)}}
                  src={folderImage}
                  key={collection.path}
                  style={{width: '120px', display: 'inline-block', marginRight: '10px'}}
                  alt="Thumbnail alt text"
                >
                  <h4>{collection.label}</h4>
                  <p>{collection.path}</p>
                </Thumbnail>
              );
            })}
          </div>}
        </div>}

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

export default connect(
  (state) => {
    return {
      viewFormat: selectFileListingViewFormat(state)
    }
  },
  (dispatch) => {
    return {
      dispatch: dispatch
    }
  }
)(Browser);

