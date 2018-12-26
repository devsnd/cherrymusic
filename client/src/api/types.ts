export interface SimpleDirectoryInterface {
    id: number,
    parent: string,
    path: string,
}

export interface MetaDataInterface {
    track: number,
    track_total: number,
    title: string,
    artist: {
        id: number,
        name: string,
    },
    album: string,
    year: number,
    genre: string,
    duration: number,
}

export interface FileInterface {
    id: number,
    filename: string,
    stream_url: string,
    meta_data: null | MetaDataInterface,
}

export interface DirectoryInterface extends SimpleDirectoryInterface {
    sub_directories: SimpleDirectoryInterface[],
    files: FileInterface[],
}
