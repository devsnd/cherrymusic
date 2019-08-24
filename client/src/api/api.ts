
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
    static basePath: string = '/api/v1';
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
        let url = Settings.getBaseUrl() + Settings.basePath + path;
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
}

type DirectoryReadArgs = {
}

export class Directory implements APIEndpoint {
    static async basedirs (params?: DirectoryBasedirsArgs) {
        return Settings.call('get', `/directory/basedirs/`, params);
    }

    static async list (params?: DirectoryListArgs) {
        return Settings.call('get', `/directory/`, params);
    }

    static async read (id: Number, params?: DirectoryReadArgs) {
        return Settings.call('get', `/directory/${id}/`, params);
    }
}

type FileListArgs = {
}

type FileReadArgs = {
}

type FileStreamArgs = {
}

type FileTranscodeArgs = {
}

export class File implements APIEndpoint {
    static async list (params?: FileListArgs) {
        return Settings.call('get', `/file/`, params);
    }

    static async read (id: Number, params?: FileReadArgs) {
        return Settings.call('get', `/file/${id}/`, params);
    }

    static async stream (id: Number, params?: FileStreamArgs) {
        return Settings.call('get', `/file/${id}/stream/`, params);
    }

    static async transcode (id: Number, params?: FileTranscodeArgs) {
        return Settings.call('get', `/file/${id}/transcode/`, params);
    }
}

type PlaylistCreateArgs = {
}

type PlaylistDeleteArgs = {
}

type PlaylistListArgs = {
}

type PlaylistPartialupdateArgs = {
}

type PlaylistReadArgs = {
}

type PlaylistUpdateArgs = {
}

export class Playlist implements APIEndpoint {
    static async create (params?: PlaylistCreateArgs) {
        return Settings.call('post', `/playlist/`, params);
    }

    static async delete (id: Number, params?: PlaylistDeleteArgs) {
        return Settings.call('delete', `/playlist/${id}/`, params);
    }

    static async list (params?: PlaylistListArgs) {
        return Settings.call('get', `/playlist/`, params);
    }

    static async partialUpdate (id: Number, params?: PlaylistPartialupdateArgs) {
        return Settings.call('patch', `/playlist/${id}/`, params);
    }

    static async read (id: Number, params?: PlaylistReadArgs) {
        return Settings.call('get', `/playlist/${id}/`, params);
    }

    static async update (id: Number, params?: PlaylistUpdateArgs) {
        return Settings.call('put', `/playlist/${id}/`, params);
    }
}

type SearchSearchArgs = {
}

export class Search implements APIEndpoint {
    static async search (params?: SearchSearchArgs) {
        return Settings.call('get', `/search/search/`, params);
    }
}

type StatusListArgs = {
}

export class Status implements APIEndpoint {
    static async list (params?: StatusListArgs) {
        return Settings.call('get', `/status/`, params);
    }
}

type TrackCreateArgs = {
}

type TrackDeleteArgs = {
}

type TrackListArgs = {
}

type TrackPartialupdateArgs = {
}

type TrackReadArgs = {
}

type TrackUpdateArgs = {
}

export class Track implements APIEndpoint {
    static async create (params?: TrackCreateArgs) {
        return Settings.call('post', `/track/`, params);
    }

    static async delete (id: Number, params?: TrackDeleteArgs) {
        return Settings.call('delete', `/track/${id}/`, params);
    }

    static async list (params?: TrackListArgs) {
        return Settings.call('get', `/track/`, params);
    }

    static async partialUpdate (id: Number, params?: TrackPartialupdateArgs) {
        return Settings.call('patch', `/track/${id}/`, params);
    }

    static async read (id: Number, params?: TrackReadArgs) {
        return Settings.call('get', `/track/${id}/`, params);
    }

    static async update (id: Number, params?: TrackUpdateArgs) {
        return Settings.call('put', `/track/${id}/`, params);
    }
}

type UserCreateArgs = {
}

type UserDeleteArgs = {
}

type UserListArgs = {
}

type UserPartialupdateArgs = {
}

type UserReadArgs = {
}

type UserUpdateArgs = {
}

export class User implements APIEndpoint {
    static async create (params?: UserCreateArgs) {
        return Settings.call('post', `/user/`, params);
    }

    static async delete (id: Number, params?: UserDeleteArgs) {
        return Settings.call('delete', `/user/${id}/`, params);
    }

    static async list (params?: UserListArgs) {
        return Settings.call('get', `/user/`, params);
    }

    static async partialUpdate (id: Number, params?: UserPartialupdateArgs) {
        return Settings.call('patch', `/user/${id}/`, params);
    }

    static async read (id: Number, params?: UserReadArgs) {
        return Settings.call('get', `/user/${id}/`, params);
    }

    static async update (id: Number, params?: UserUpdateArgs) {
        return Settings.call('put', `/user/${id}/`, params);
    }
}

type YoutubeSearchArgs = {
}

export class Youtube implements APIEndpoint {
    static async search (params?: YoutubeSearchArgs) {
        return Settings.call('get', `/youtube/search/`, params);
    }
}


