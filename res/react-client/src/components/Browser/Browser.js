import React, {PropTypes} from 'react';
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
import ScrollableView from 'components/ScrollableView/ScrollableView';
import SpinnerImage from 'static/img/cherrymusic_loader.gif';
import classes from './Browser.scss';
import folderImage from 'static/img/folder.png';

export class Browser extends React.Component {
  static propTypes = {
    // attr
    height: PropTypes.number,
  };

  constructor (props) {
    super(props);
    this.state = {};
    this.selectAll = (trackIds) => {
      for (const trackId of trackIds) {
        this.props.selectTrack(trackId);
      }
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
        <div ref="header">
          <Breadcrumb style={{marginBottom: '5px'}}>
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
            <Button active={viewFormatList} onClick={this.props.setListView} bsSize="small">
              List
            </Button>
            <Button active={viewFormatTile} onClick={this.props.setTileView} bsSize="small">
              Tile
            </Button>
          </ButtonGroup>
        </div>
        <ScrollableView
          height={
            this.props.height - 81 /* breadcrumbs and sort buttons */
          }
        >
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
                          <img
                            src={folderImage}
                            style={{
                              float: 'left',
                              paddingRight: 10,
                              height: '36px',
                            }} />
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
            <Button onClick={() => {this.selectAll(tracks)}} style={{marginBottom: '10px'}}>
              Add all to playlist
            </Button>
            <table className="table table-hover" style={{display: 'inline-block'}}>
              <tbody style={{display: 'inline-block', width: '100%'}}>
              {tracks.map((trackId) => {
                const track = entities.track[trackId];
                return (
                  <tr key={trackId} style={{
                    display: 'inline-block',
                    width: '100%',
                    overflow: 'hidden'
                  }}>
                    <td style={{display: 'block'}}>
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
          </div>}
        </ScrollableView>
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
      setListView: () => dispatch(actionSetFileListingViewFormat(FileListingViewFormats.List)),
      setTileView: () => dispatch(actionSetFileListingViewFormat(FileListingViewFormats.Tile)),
    }
  }
)(Browser);

