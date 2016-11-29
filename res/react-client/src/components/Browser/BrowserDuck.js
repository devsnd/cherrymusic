const SET_FILE_LISTING_VIEW_FORMAT = 'abend/redux/SET_FILE_LIST_VIEW_FORMAT';

export const FileListingViewFormats = {
  List: 'List',
  Tile: 'Tile',
};

export const initialState = {
  fileListingViewFormat: FileListingViewFormats.Tile,
};

export function actionSetFileListingViewFormat (format) {
  return {type: SET_FILE_LISTING_VIEW_FORMAT, payload: {format: format } };
}

function select (state) {
  return state.browser;
}

export function selectFileListingViewFormat (state) {
  return select(state).fileListingViewFormat;
}

const ACTION_HANDLERS = {
  [SET_FILE_LISTING_VIEW_FORMAT]: (state, action) => {
    return {
      ...state,
      fileListingViewFormat: action.payload.format,
    };
  },
};

export default function (state = initialState, action) {
  const handler = ACTION_HANDLERS[action.type];
  return handler ? handler(state, action) : state;
}

