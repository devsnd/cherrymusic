
//
//  AUTO-GENERATED API INTERFACE
//
//  To add an endpoint, please implement the endpoint in the server and then
//  regenerate this file by calling:
//
//      make generate_api
//

import * as _ from 'lodash';
import {dict} from "@/common/utils";


export abstract class APIEndpoint {
}


type HTTPMethod = 'get' | 'post' | 'delete' | 'patch' | 'put';


export class Settings {
    static baseUrl: string = '';
    private static authtoken: string | null = null;

    static setBaseUrl (baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    static getBaseUrl (): string {
        return this.baseUrl;
    }
    
    static setAuthtoken (authtoken: string) {
        this.authtoken = authtoken;
    }
    
    static getAuthToken (): string | null {
        return this.authtoken;
    }
    
    static encodeGetParams (params: {[key:string]: string}): string {
      return (
          Object.entries(params)
          .map(([key, value]) => (key + '=' + encodeURIComponent(value)))
          .join("&")
      );
    }

    static async call (method: HTTPMethod, path: string, data?: any) {
        let url = Settings.getBaseUrl() + path;
        let options: any = {
            method: method,
            headers: new Headers({'content-type': 'application/json'}),
        };
        if (data === undefined) {
            data = {};
        }
        if (Settings.authtoken !== null) {
            data.authtoken = Settings.authtoken;
        }
        
        // map all calls to snake case
        data = dict(Object.entries(data).map((elem: any) => [_.snakeCase(elem[0]), elem[1]]));

        if (method === 'post') {
            options = {...options, body: JSON.stringify(data)};
        } else if (method === 'get') {
            url = url + '?' + Settings.encodeGetParams(data);        
        }

        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(response.statusText)
        }
        return response.json()
    }
}

// generate the argument types for each api call which

type DirectoryBasedirsArgs = {
}

type DirectoryListArgs = {
    limit?: Number,
    offset?: Number,
    basedir?: string,
}

type DirectoryReadArgs = {
    basedir?: string,
}

export class Directory implements APIEndpoint {
    static async basedirs (params?: DirectoryBasedirsArgs) {
        return Settings.call('get', `/api/v1/directory/basedirs/`, params);
    }

    static async list (params?: DirectoryListArgs) {
        return Settings.call('get', `/api/v1/directory/`, params);
    }

    static async read (id: Number, params?: DirectoryReadArgs) {
        return Settings.call('get', `/api/v1/directory/${id}/`, params);
    }
}

type FileListArgs = {
    limit?: Number,
    offset?: Number,
}

type FileReadArgs = {
}

type FileStreamArgs = {
}

type FileTranscodeArgs = {
}

export class File implements APIEndpoint {
    static async list (params?: FileListArgs) {
        return Settings.call('get', `/api/v1/file/`, params);
    }

    static async read (id: Number, params?: FileReadArgs) {
        return Settings.call('get', `/api/v1/file/${id}/`, params);
    }

    static async stream (id: Number, params?: FileStreamArgs) {
        return Settings.call('get', `/api/v1/file/${id}/stream/`, params);
    }

    static async transcode (id: Number, params?: FileTranscodeArgs) {
        return Settings.call('get', `/api/v1/file/${id}/transcode/`, params);
    }
}

type PlaylistCreateArgs = {
}

type PlaylistDeleteArgs = {
}

type PlaylistListArgs = {
    limit?: Number,
    offset?: Number,
}

type PlaylistPartialupdateArgs = {
}

type PlaylistReadArgs = {
}

type PlaylistUpdateArgs = {
}

export class Playlist implements APIEndpoint {
    static async create (params?: PlaylistCreateArgs) {
        return Settings.call('post', `/api/v1/playlist/`, params);
    }

    static async delete (id: Number, params?: PlaylistDeleteArgs) {
        return Settings.call('delete', `/api/v1/playlist/${id}/`, params);
    }

    static async list (params?: PlaylistListArgs) {
        return Settings.call('get', `/api/v1/playlist/`, params);
    }

    static async partialUpdate (id: Number, params?: PlaylistPartialupdateArgs) {
        return Settings.call('patch', `/api/v1/playlist/${id}/`, params);
    }

    static async read (id: Number, params?: PlaylistReadArgs) {
        return Settings.call('get', `/api/v1/playlist/${id}/`, params);
    }

    static async update (id: Number, params?: PlaylistUpdateArgs) {
        return Settings.call('put', `/api/v1/playlist/${id}/`, params);
    }
}

type SearchSearchArgs = {
    query: string,
}

export class Search implements APIEndpoint {
    static async search (params?: SearchSearchArgs) {
        return Settings.call('get', `/api/v1/search/search/`, params);
    }
}

type StatusListArgs = {
}

export class Status implements APIEndpoint {
    static async list (params?: StatusListArgs) {
        return Settings.call('get', `/api/v1/status/`, params);
    }
}

type TrackCreateArgs = {
}

type TrackDeleteArgs = {
}

type TrackListArgs = {
    limit?: Number,
    offset?: Number,
}

type TrackPartialupdateArgs = {
}

type TrackReadArgs = {
}

type TrackUpdateArgs = {
}

export class Track implements APIEndpoint {
    static async create (params?: TrackCreateArgs) {
        return Settings.call('post', `/api/v1/track/`, params);
    }

    static async delete (id: Number, params?: TrackDeleteArgs) {
        return Settings.call('delete', `/api/v1/track/${id}/`, params);
    }

    static async list (params?: TrackListArgs) {
        return Settings.call('get', `/api/v1/track/`, params);
    }

    static async partialUpdate (id: Number, params?: TrackPartialupdateArgs) {
        return Settings.call('patch', `/api/v1/track/${id}/`, params);
    }

    static async read (id: Number, params?: TrackReadArgs) {
        return Settings.call('get', `/api/v1/track/${id}/`, params);
    }

    static async update (id: Number, params?: TrackUpdateArgs) {
        return Settings.call('put', `/api/v1/track/${id}/`, params);
    }
}

type UserCreateArgs = {
}

type UserDeleteArgs = {
}

type UserListArgs = {
    limit?: Number,
    offset?: Number,
}

type UserPartialupdateArgs = {
}

type UserReadArgs = {
}

type UserUpdateArgs = {
}

export class User implements APIEndpoint {
    static async create (params?: UserCreateArgs) {
        return Settings.call('post', `/api/v1/user/`, params);
    }

    static async delete (id: Number, params?: UserDeleteArgs) {
        return Settings.call('delete', `/api/v1/user/${id}/`, params);
    }

    static async list (params?: UserListArgs) {
        return Settings.call('get', `/api/v1/user/`, params);
    }

    static async partialUpdate (id: Number, params?: UserPartialupdateArgs) {
        return Settings.call('patch', `/api/v1/user/${id}/`, params);
    }

    static async read (id: Number, params?: UserReadArgs) {
        return Settings.call('get', `/api/v1/user/${id}/`, params);
    }

    static async update (id: Number, params?: UserUpdateArgs) {
        return Settings.call('put', `/api/v1/user/${id}/`, params);
    }
}

type YoutubeSearchArgs = {
    query: string,
}

export class Youtube implements APIEndpoint {
    static async search (params?: YoutubeSearchArgs) {
        return Settings.call('get', `/api/v1/youtube/search/`, params);
    }
}


