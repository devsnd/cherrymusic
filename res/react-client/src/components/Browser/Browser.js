import React, {PropTypes } from 'react';
import {connect } from 'react-redux';
import PureRenderMixin from 'react-addons-pure-render-mixin';
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
  Glyphicon,
} from 'react-bootstrap';

import {LoadingStates } from 'redux/modules/CherryMusicApi';
import TrackListItem from 'components/TrackListItem/TrackListItem';
import ScrollableView from 'components/ScrollableView/ScrollableView';
import SpinnerImage from 'static/img/cherrymusic_loader.gif';
import classes from './Browser.scss';
import AlbumArt from 'components/AlbumArt/AlbumArt';
import folderImage from 'static/img/folder.png';

export class Browser extends React.Component {
  static propTypes = {
    // attr
    height: PropTypes.number,
  };

  constructor (props) {
    super(props);
    this.shouldComponentUpdate = PureRenderMixin.shouldComponentUpdate.bind(this);

    this.state = {
      // lastMove determines how to animate when navigating (e.g. LTR or RTL)
      lastMove: 'child',  // 'parent' || 'child'
    };
    this.selectAll = (trackIds) => {
      for (const trackId of trackIds) {
        this.props.selectTrack(trackId);
      }
    };
  }

  render () {
    const {collections, compacts, tracks, entities, state, path } = this.props.fileBrowser;
    const {loadDirectory, selectTrack } = this.props;

    // build breadcrumbs
    const breadCrumbs = [
      {label: 'basedir', path: '' },
    ];
    if (path) {
      const splitPaths = path.split('/');
      let fullPath = null;
      for (let i = 0; i < splitPaths.length; i++) {
        const label = splitPaths[i];
        let fullPathToPart;
        if (i === 0) {
          fullPath = splitPaths[i];
        } else {
          fullPath = fullPath + '/' + splitPaths[i];
        }
        breadCrumbs.push({label: label, path: fullPath });
      }
    }
    const parentPath = path ? path.split('/').slice(0, -1).join('/') : null;
    const parentPathHandler = () => {
      this.setState({lastMove: 'parent' });
      loadDirectory(parentPath);
    };
    const handleOpenChildFolder = (path) => () => {
      this.setState({lastMove: 'child' });
      loadDirectory(path);
    };

    const viewFormatList = this.props.viewFormat === FileListingViewFormats.List;
    const viewFormatTile = this.props.viewFormat === FileListingViewFormats.Tile;

    return (
      <div>
        <div ref="header">
          <Breadcrumb style={{marginBottom: '5px' }}>
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
          <div style={{marginBottom: '10px', height: '30px' }}>
            {parentPath !== null &&
              <Button
                onClick={parentPathHandler}
                bsSize="small">
                  <Glyphicon glyph="arrow-left" /> go back
              </Button>
            }
            <ButtonGroup style={{float: 'right' }}>
              <Button active={viewFormatList} onClick={this.props.setListView} bsSize="small">
                <Glyphicon glyph="th-list" />
              </Button>
              <Button active={viewFormatTile} onClick={this.props.setTileView} bsSize="small">
                <Glyphicon glyph="th-large" />
              </Button>
            </ButtonGroup>
          </div>
        </div>
        {state === LoadingStates.loading &&
          <img src={SpinnerImage} style={{
            left: '50%',
            marginLeft: '-40px',
            position: 'relative',
          }} />
        }
        {state !== LoadingStates.loading &&
        <ScrollableView
          height={
            this.props.height - 83 /* breadcrumbs and sort buttons */
          }
          className={
            this.state.lastMove === 'parent' ? classes.moveInLeft : classes.moveInRight
          }
          style={{
            paddingRight: 10
          }}
        >
          {!collections.length && !compacts.length && !tracks.length && (
            <p>No playable media files found</p>
          )}
          {!!collections.length && <div>
            {viewFormatList &&
            <ListGroup>
              {collections.map((collectionId, idx) => {
                const firstItem = idx === 0;
                const lastItem = idx === collections.length;
                const collection = entities.collection[collectionId];
                return (
                  <ListGroupItem className="list-group-item"
                    key={collection.path}
                    onClick={handleOpenChildFolder(collection.path)}
                    style={{
                      padding: 0,
                      height: 52,
                    }}
                  >
                    <table className={classes.nopadTable}><tbody><tr>
                      <td>
                        <AlbumArt
                          directory={collection.path}
                          /* round the corner of the first and last items */
                          style={{
                            borderTopLeftRadius: firstItem ? 4 : 0,
                            borderBottomLeftRadius: lastItem ? 4 : 0
                          }}
                        />
                      </td>
                      <td>
                        <span className={classes.nowrap} style={{paddingLeft: '10px'}}>
                          {collection.label}
                        </span>
                        <br />
                        <span className={classes.nowrap} style={{paddingLeft: '10px'}}>
                            <small>{collection.path}</small>
                        </span>
                      </td>
                    </tr></tbody></table>
                  </ListGroupItem>
                );
              })}
            </ListGroup>
            }
            {viewFormatTile && <div>
              {collections.map((collectionId) => {
                const collection = entities.collection[collectionId];
                return (
                  <div
                    className={classes.hoverItem}
                    onClick={handleOpenChildFolder(collection.path)}
                    key={collection.path}
                    style={{
                      width: '100px',
                      display: 'inline-block',
                      overflow: 'hidden',
                      border: '1px solid #eee',
                      borderRadius: 5,
                      verticalAlign: 'top',
                      marginRight: 10,
                      marginBottom: 5,
                    }}
                    alt="Thumbnail alt text"
                  >
                    <div style={{
                      position: 'relative',
                    }}>
                      <AlbumArt
                        directory={collection.path}
                        style={{
                          width: 100,
                          height: 100,
                        }}
                      />
                      <div
                        style={{
                          position: 'absolute',
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: 'rgba(255,255,255,0.8)',
                        }}
                      >
                        <h4 style={{padding: '0 5px' }}>{collection.label}</h4>
                      </div>
                    </div>
                    <p style={{fontSize: 11, padding: '5px 5px 0 5px' }}>
                      {collection.path}
                    </p>
                  </div>
                );
              })}
            </div>}
          </div>}

          {!!compacts.length && <div>
            {viewFormatList &&
            <ListGroup>
              {compacts.map((compactId) => {
                const compact = entities.compact[compactId];
                return (
                  <ListGroupItem
                    key={compact.path}
                    onClick={() => { loadDirectory(compact.urlpath, compact.label); }}
                    header={
                      <span>
                        {compact.label}
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
                    {compact.path}
                  </ListGroupItem>
                );
              })}
            </ListGroup>
            }
            {viewFormatTile && <div>
              {compacts.map((compactId) => {
                const compact = entities.compact[compactId];
                return (
                  <Thumbnail
                    onClick={() => { loadDirectory(compact.urlpath, compact.label); }}
                    src={folderImage}
                    key={compact.path}
                    style={{width: '120px', display: 'inline-block', marginRight: '10px' }}
                    alt="Thumbnail alt text"
                  >
                    <h4>{compact.label}</h4>
                    <p>{compact.path}</p>
                  </Thumbnail>
                );
              })}
            </div>}
          </div>}

          {!!tracks.length && <div>
            <Button
              onClick={() => { this.selectAll(tracks); }}
              style={{marginBottom: '10px' }}
              bsStyle="primary"
            >
              Add all to playlist
            </Button>
            <table className="table table-hover"
              style={{display: 'inline-block' }}>
              <tbody style={{display: 'inline-block', width: '100%' }}>
              {tracks.map((trackId) => {
                const track = entities.track[trackId];
                return (
                  <tr key={trackId} style={{
                    display: 'inline-block',
                    width: '100%',
                    overflow: 'hidden',
                  }}>
                    <td style={{display: 'block' }}>
                      <TrackListItem
                        track={track}
                        onClick={() => { selectTrack(trackId); }}
                      />
                    </td>
                  </tr>
                );
              })}
              </tbody>
            </table>
          </div>}
        </ScrollableView>
        }
      </div>
    );
  }
}

export default connect(
  (state) => {
    return {
      viewFormat: selectFileListingViewFormat(state),
    };
  },
  (dispatch) => {
    return {
      setListView: () => dispatch(actionSetFileListingViewFormat(FileListingViewFormats.List)),
      setTileView: () => dispatch(actionSetFileListingViewFormat(FileListingViewFormats.Tile)),
    };
  }
)(Browser);

