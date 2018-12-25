


//
//  AUTO-GENERATED API INTERFACE
//
//  To add an endpoint, please implement the endpoint in the server and then
//  regenerate this file by calling:
//
//      make generate_api
//

export module API {

    export class Settings {
        static baseUrl: string = '';

        static setBaseUrl (baseUrl: string) {
            this.baseUrl = baseUrl;
        }

        static getBaseUrl (): string {
            return this.baseUrl;
        }

        static async call (method: string, path: string, data?: any) {
            const url = Settings.getBaseUrl() + path;
            let options: any = {
                method: method,
            }
            if (data) {
                options = {...options, body: JSON.stringify(data)};
            }
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(response.statusText)
            }
            return response.json()
        }
    }

    
    export class Directory {
        static async list () {
            return Settings.call('get', `/api/v1/directory/`);
        }

        static async read (id: Number) {
            return Settings.call('get', `/api/v1/directory/${id}/`);
        }
    }
    
    export class File {
        static async list () {
            return Settings.call('get', `/api/v1/file/`);
        }

        static async read (id: Number) {
            return Settings.call('get', `/api/v1/file/${id}/`);
        }

        static async stream (id: Number) {
            return Settings.call('get', `/api/v1/file/${id}/stream/`);
        }

        static async transcode (id: Number) {
            return Settings.call('get', `/api/v1/file/${id}/transcode/`);
        }
    }
    
    export class Playlist {
        static async create () {
            return Settings.call('post', `/api/v1/playlist/`);
        }

        static async delete (id: Number) {
            return Settings.call('delete', `/api/v1/playlist/${id}/`);
        }

        static async list () {
            return Settings.call('get', `/api/v1/playlist/`);
        }

        static async partialUpdate (id: Number) {
            return Settings.call('patch', `/api/v1/playlist/${id}/`);
        }

        static async read (id: Number) {
            return Settings.call('get', `/api/v1/playlist/${id}/`);
        }

        static async update (id: Number) {
            return Settings.call('put', `/api/v1/playlist/${id}/`);
        }
    }
    
    export class Status {
        static async list () {
            return Settings.call('get', `/api/v1/status/`);
        }
    }
    
    export class Track {
        static async create () {
            return Settings.call('post', `/api/v1/track/`);
        }

        static async delete (id: Number) {
            return Settings.call('delete', `/api/v1/track/${id}/`);
        }

        static async list () {
            return Settings.call('get', `/api/v1/track/`);
        }

        static async partialUpdate (id: Number) {
            return Settings.call('patch', `/api/v1/track/${id}/`);
        }

        static async read (id: Number) {
            return Settings.call('get', `/api/v1/track/${id}/`);
        }

        static async update (id: Number) {
            return Settings.call('put', `/api/v1/track/${id}/`);
        }
    }
    
    export class User {
        static async create () {
            return Settings.call('post', `/api/v1/user/`);
        }

        static async delete (id: Number) {
            return Settings.call('delete', `/api/v1/user/${id}/`);
        }

        static async list () {
            return Settings.call('get', `/api/v1/user/`);
        }

        static async partialUpdate (id: Number) {
            return Settings.call('patch', `/api/v1/user/${id}/`);
        }

        static async read (id: Number) {
            return Settings.call('get', `/api/v1/user/${id}/`);
        }

        static async update (id: Number) {
            return Settings.call('put', `/api/v1/user/${id}/`);
        }
    }
    
}
