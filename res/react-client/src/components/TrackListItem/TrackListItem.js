/**
 * Created by tom on 5/23/16.
 */
import React, {PropTypes } from 'react';

import { Glyphicon } from 'react-bootstrap';

import {MetaDataLoadingStates, selectTrackMetaDataLoadingState } from 'redux/modules/CherryMusicApi';
import Duration from 'components/Duration/Duration';
import classes from './TrackListItem.scss';

class TrackListItem extends React.Component {
  static propTypes = {
    track: PropTypes.object.isRequired,
    compact: PropTypes.bool,
  };

  constructor (props) {
    super(props);
  }

  zeropad (n, zeros = 1) {
    if (n < 10) {
      return '0' * zeros + n;
    }
    return n;
  }

  render () {
    const {track } = this.props;
    const metaLoadState = selectTrackMetaDataLoadingState(track);
    const validMetaData = (
      metaLoadState === MetaDataLoadingStates.loaded
      && (
        track.metadata.artist.length
        ||
        track.metadata.title.length
      )
    );

    return (
      <table className={classes.TrackListItem} {...this.props}>
        <tbody>
          {metaLoadState === MetaDataLoadingStates.idle &&
            <tr>
              <td><Glyphicon glyph="time" /></td>
              <td>{track.label}</td>
            </tr>
          }
          {metaLoadState === MetaDataLoadingStates.loading &&
            <tr>
              <td><Glyphicon glyph="refresh" /></td>
              <td>{track.label}</td>
            </tr>
          }
          {metaLoadState === MetaDataLoadingStates.loaded &&
            <tr>
              <td className={classes.Duration}>
                <Duration seconds={track.metadata.length} />
              </td>
              <td>
                {track.metadata.track !== '' &&
                  <span>{this.zeropad(track.metadata.track)} </span>
                }
                {track.metadata.artist.length > 0 &&
                  <span>{track.metadata.artist} - </span>
                }
                {track.metadata.title.length !== 0 &&
                  <span>{track.metadata.title}</span>
                }
                {track.metadata.artist.length === 0 &&
                  <span>{track.label}</span>
                }
              </td>
            </tr>
          }
          {!this.props.compact && (
            <tr>
              <td />
              <th colSpan={3} className={classes.Path}>
                {track.path}
              </th>
            </tr>
          )}
        </tbody>
      </table>
    );
  }
}

export default TrackListItem;
