CherryMusic API Reference v1
============================

Files
-----

### List all files
```
GET /api/v1/file
```

**Response**

```
Status: 200 OK
```
```
[
    {
        "id": 1,
        "filename": "06.- Astronauta.mp3",
        "path": "Paisano/Revolucion/06.- Astronauta.mp3",
        "meta_track": "06",
        "meta_track_total": "13",
        "meta_title": "Astronauta",
        "meta_artist": "Paisano",
        "meta_album": "Revolucion",
        "meta_year": "2014",
        "meta_genre": "Acustico",
        "meta_duration": 238.236734693878,
        "meta_index_date": "2016-01-12"
    }
]
```

### Get a single file
```
GET /api/v1/file/<id>
```

**Response**

```
Status: 200 OK
```
```
{
    "id": 1,
    "filename": "06.- Astronauta.mp3",
    "path": "Paisano/Revolucion/06.- Astronauta.mp3",
    "meta_track": "06",
    "meta_track_total": "13",
    "meta_title": "Astronauta",
    "meta_artist": "Paisano",
    "meta_album": "Revolucion",
    "meta_year": "2014",
    "meta_genre": "Acustico",
    "meta_duration": 238.236734693878,
    "meta_index_date": "2016-01-12"
}
```


Directories
-----

### List all directories
```
GET /api/v1/directory
```

**Response**

```
Status: 200 OK
```
```
[
    {
        "parent": null,
        "path": null,
        "id": 1
    },
    {
        "parent": 1,
        "path": "Paisano",
        "id": 2
    }
]
```

### Get a single directory
```
GET /api/v1/directory/<id>
```

**Response**

```
Status: 200 OK
```
```
{
    "parent": 1,
    "path": "Paisano",
    "id": 2
}
```


Playlists
---------

### List all playlists
```
GET /api/v1/playlist
```

**Response**

```
Status: 200 OK
```
```
[
    {
        "id": 1,
        "name": "Paisano",
        "owner": 1,
        "owner_name": "admin",
        "public": true,
        "created_at": "2016-01-12T12:40:41.710961Z"
    },
]
```

### Get a single playlist
```
GET /api/v1/playlist/<id>
```

**Response**

```
Status: 200 OK
```
```
{
    "id": 1,
    "name": "Paisano",
    "owner": 1,
    "public": true,
    "tracks": [
        {
            "playlist": 1,
            "order": 0,
            "type": 0,
            "file": 1,
            "data": {
                "id": 1,
                "filename": "06.- Astronauta.mp3",
                "path": "Paisano/Revolucion/06.- Astronauta.mp3",
                "meta_track": "06",
                "meta_track_total": "13",
                "meta_title": "Astronauta",
                "meta_artist": "Paisano",
                "meta_album": "Revolucion",
                "meta_year": "2014",
                "meta_genre": "Acustico",
                "meta_duration": 238.236734693878,
                "meta_index_date": "2016-01-12"
            }
        }
    ],
    "owner_name": "admin",
    "created_at": "2016-01-12T12:40:41.710961Z"
}
```

### Create playlist
```
POST /api/v1/playlist
```
**Parameters**

| Name | Type | Description |
|:----------:|:-----------:|:------------|
| name | *string* | **Required.** The name of the new playlist|    
| tracks | *array of tracks* | **Required.** Array of tracks objects|   
| public | bool | Make playlist public to other users. |

**Example**

```
{
    "name": "TestPlaylist",
    "tracks":[
        {
            "type": 0,
            "data":{
                "id":1
            }
        }
    ],
    "public": false
}
```

**Response**

```
Status: 201 CREATED
```

```
{
    "id": 2,
    "name": "TestPlaylist",
    "owner": 1,
    "public": false,
    "owner_name": "admin",
    "tracks":[
        {
            "type": 0,
            "order": 0,
            "playlist": 2,
            "file": 1,
            "data":{
                "id":1,
                "filename": "06.- Astronauta.mp3",
                "path": "Paisano/Revolucion/06.- Astronauta.mp3",
                "meta_track": "06",
                "meta_track_total": "13",
                "meta_title": "Astronauta",
                "meta_artist": "Paisano",
                "meta_album": "Revolucion",
                "meta_year": "2014",
                "meta_genre": "Acustico",
                "meta_duration": 238.236734693878,
                "meta_index_date": "2016-01-12"
            }
        }
    ],
    "created_at": "2016-01-12T12:50:42.710961Z"
}
```

### Update playlist
```
POST /api/v1/playlist/<id>
```
**Parameters**

| Name | Type | Description |
|:----------:|:-----------:|:------------|
| name | *string* | The new name of the playlist|    
| tracks | *array of tracks* | The new tracks of the playlist|   
| public | bool | Make playlist public to other users. |

**Example**

```
{
    "name": "TestPlaylist2",
    "tracks":[
        {
            "type": 0,
            "data":{
                "id":1
            }
        }
    ],
    "public": true
}
```

**Response**

```
Status: 200 OK
```

```
{
    "id": 2,
    "name": "TestPlaylist2",
    "owner": 1,
    "public": true,
    "owner_name": "admin",
    "tracks":[
        {
            "type": 0,
            "order": 0,
            "playlist": 2,
            "file": 1,
            "data":{
                "id":1,
                "filename": "06.- Astronauta.mp3",
                "path": "Paisano/Revolucion/06.- Astronauta.mp3",
                "meta_track": "06",
                "meta_track_total": "13",
                "meta_title": "Astronauta",
                "meta_artist": "Paisano",
                "meta_album": "Revolucion",
                "meta_year": "2014",
                "meta_genre": "Acustico",
                "meta_duration": 238.236734693878,
                "meta_index_date": "2016-01-12"
            }
        }
    ],
    "created_at": "2016-01-12T12:50:42.710961Z"
}
```



User
----

### List all users
Must be **superuser**
```
GET /api/v1/user
```

**Response**

```
Status: 200 OK
```
```
[
    {
        "id": 1,
        "username": "admin",
        "last_login": "2016-01-13T01:18:48.411511Z",
        "is_logged": true,
        "is_superuser": true
    },
    {
        "id": 2,
        "username": "foo",
        "last_login": "2016-01-13T01:22:40.411511Z",
        "is_logged": true,
        "is_superuser": false
    },
]
```

If user is **not superuser** only gets its own user.
**Response**

```
Status: 200 OK
```
```
[
    {
        "id": 2,
        "username": "foo",
        "last_login": "2016-01-13T01:22:40.411511Z",
        "is_logged": true,
        "is_superuser": false
    },
]
```

### Get a single user
Must be **superuser** to see all, if user are not, user only can access its own.
```
GET /api/v1/user/<id>
```

**Response**

```
Status: 200 OK
```
```
{
    "id": 2,
    "username": "foo",
    "last_login": "2016-01-13T01:22:40.411511Z",
    "is_logged": true,
    "is_superuser": false
}
```

### Create user
```
POST /api/v1/user
```
**Parameters**

| Name | Type | Description |
|:----------:|:-----------:|:------------|
| username | *string* | **Required.** New user name|    
| password | *string* | **Required.** New user password|   
| email | string | New user email. |
| is_superuser | bool | Make user superuser. |

**Example**

```
{
    "username": "test",
    "password": "test",
    "is_superuser": false,
    "email": "test@test.com",
}
```

**Response**

```
Status: 201 CREATED
```

```
{
    "id": 3,
    "username": "test",
    "password": "test",
    "is_superuser": false,
    "email": "test@test.com",
}
```



