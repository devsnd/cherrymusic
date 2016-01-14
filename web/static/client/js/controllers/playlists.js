app.controller('PlaylistsCtrl', function($scope, $rootScope, $uibModal, $filter, Playlist, Track, Upload, $timeout) {

    $scope.openSavePlaylistModal = function(){
        var uibModalInstance = $uibModal.open({
            animation: true,
            templateUrl: STATIC_FILES + 'client/modals/save_playlist.html',
            scope: $scope,
            controller: function($scope, $uibModalInstance){
                $scope.isPublic = false;

                var getPlaylistTitle = function(){
                    var currentName = $scope.currentPlaylist.name;

                    if(currentName == 'Queue' || currentName == 'New Playlist'){
                        return undefined;
                    };
                    return currentName;
                };

                $scope.newPlaylistTitle = getPlaylistTitle();

                $scope.close = function(){
                    $uibModalInstance.dismiss('cancel');
                };

                $scope.savePlaylist = function(playlist, title, isPublic){
                    $scope.$emit('CREATE_PLAYLIST', playlist, title, isPublic); 
                    $scope.close();
                } 
            }
        });
    };

    Playlist.query(function(playlists){
            $scope.playlists = playlists;
            $rootScope.loadingPlaylistbrowser = false;
    });

    $scope.currentTrackIndex = 0;

    $scope.isShuffle = false;
    $scope.isRepeat = false;

    $scope.toggleShuffle = function() {
        if ($scope.isShuffle){
            $scope.isShuffle = false;
        }
        else{
            $scope.isShuffle = true;
        };
    };

    $scope.toggleRepeat = function() {
        if ($scope.isRepeat){
            $scope.isRepeat = false;
        }
        else{
            $scope.isRepeat = true;
        };
    };

    var infinite = 1000000000;

    $scope.updateRemainingPlaylistPercentage = function(remainingTrackDuration){
        var remainingPlaylistDuration = remainingTrackDuration + getRemainingDurationOfTracks();
            
        if( remainingPlaylistDuration > infinite){
            $scope.remainingPlaylistDuration = undefined;
        }
        else{
            $scope.remainingPlaylistDuration = remainingPlaylistDuration;
        };
        $scope.remainingPlaylistPercentage = (1 - (remainingPlaylistDuration / getTotalDurationOfTracks())) * 100;
    };

    var getRemainingDurationOfTracks = function () {
        if($scope.isShuffle){
            return infinite;
        };

        var remainingTracks = getRemainingTracks($scope.currentPlayingPlaylist.tracks, $scope.currentPlayingTrack)

        return getTotalDuration(remainingTracks);
    };

    var getRemainingTracks = function(tracks, currentTrack){
        var remainingTracks = [];
        var isRemainingTrack = false;

        tracks.forEach(function(track, index){
            if(isRemainingTrack){
                remainingTracks.push(track);
            }
            else if(track == currentTrack){
                isRemainingTrack = true;
            };
        });

        return remainingTracks;
    }

    var getTotalDurationOfTracks = function () {
        return getTotalDuration($scope.currentPlayingPlaylist.tracks);
    };

    var getTotalDuration = function(tracks){
        var time = 0;

        tracks.forEach(function(track){
            time += track.data.meta_duration;
        });

        return time;
    };

    var createEmptyPlaylist = function(name, type){
        return {tracks: [], name: name, type: type, saved: true};
    };

    $scope.createNewPlaylist = function(){
        var newPlaylist = createEmptyPlaylist('New Playlist', 'playlist');
        $scope.openedPlaylists.push(newPlaylist);
        $scope.setCurrentPlaylist(newPlaylist);
        $scope.indexHistory = [];
    };

    $scope.clearPlaylist = function(playlist){
        playlist.tracks = [];
    };

    $scope.removedPlayed = function(playlist){
        playlist.tracks.splice(0, $scope.currentTrackIndex);
        $scope.currentTrackIndex = 0;
        $scope.indexHistory = [];
    };

    var getIsPlaylistInList = function(playlist, playlists){
        var playlistId = playlist.id;

        var isAlreadyLoadedPlaylist = _.find(playlists, function(playlist){
                return playlist.id == playlistId 
            });

        return isAlreadyLoadedPlaylist;
    };

    $scope.setCurrentPlaylist = function(playlist){
        var isAlreadyLoadedPlaylist = getIsPlaylistInList(playlist, $scope.openedPlaylists);

        if(!isAlreadyLoadedPlaylist){
            $scope.openedPlaylists.push(playlist);
        };

        $scope.currentPlaylist = playlist;
        if($scope.currentPlaylist == $scope.currentPlayingPlaylist){
            $scope.currentTrackIndex = $scope.currentPlayingTrackIndex
        }
        else{
            $scope.currentTrackIndex = 0;
        }
    };

    var defaultPlaylist = createEmptyPlaylist('Queue', 'queue')
    $scope.playlists = [];
    $scope.openedPlaylists = [defaultPlaylist];
    $scope.setCurrentPlaylist(defaultPlaylist);
    $scope.indexHistory = [];

    $scope.$on('CREATE_PLAYLIST', function(event, playlist, title, isPublic){
        var newPlaylist = angular.copy(playlist);
        newPlaylist.name = title;
        newPlaylist.public = isPublic;

        Playlist.save(newPlaylist, function(createdPlaylist){
            $scope.$emit('RELOAD_PLAYLIST', createdPlaylist);
        });
    });

    $scope.$on('RELOAD_PLAYLIST', function(event, playlist){
        Playlist.get({id: playlist.id}, function(playlist_data){
                playlist.loading = false;
                playlist.tracks = playlist_data.tracks;
                playlist.saved = true;

                var openedPlaylistIndex = getPlaylistIndex(playlist, $scope.openedPlaylists)
                $scope.openedPlaylists

                $scope.openedPlaylists.push(playlist);
                $scope.playlists.push(playlist);
                $scope.setCurrentPlaylist(playlist);
            });
    });

    $scope.$on ('REMOVE_PLAYLIST', function(event, playlist){
        var answer = confirm("Are you sure you want to remove this playlist?")
        if (!answer) {
            return;
        };

        var isAlreadyLoadedPlaylist = getIsPlaylistInList(playlist, $scope.openedPlaylists);

        if(isAlreadyLoadedPlaylist){
            var index = getPlaylistIndex(playlist);
            $scope.openedPlaylists.splice(index, 1);
            if($scope.currentPlaylist.id == playlist.id){
                $scope.setCurrentPlaylist($scope.openedPlaylists[index - 1]);
            };
        };

        Playlist.remove({id: playlist.id}, function(){
            var removedPlaylistIndex = getPlaylistIndex(playlist, $scope.playlists)
            $scope.playlists.splice(removedPlaylistIndex, 1);
        });
    });

    var getPlaylistIndex = function(playlist, playlists){
        if(playlists == undefined){
            playlists = $scope.openedPlaylists;
        };

        var index = playlists.map(function(element){
                return element.id;
            }).indexOf(playlist.id);
        return index;
    };

    $scope.updatePlaylist = function(playlist){
        $scope.$emit('UPDATE_PLAYLIST', playlist);
    };

    $scope.$on('UPDATE_PLAYLIST', function(event, playlist){
        Playlist.update({ id:playlist.id}, playlist, function(){
            var updatedPlaylistIndex = getPlaylistIndex(playlist, $scope.playlists)
            $scope.playlists.splice(updatedPlaylistIndex, 1);
            $scope.playlists.push(playlist);
            playlist.saved = true;
        });
    });

    $scope.$on('LOAD_PLAYLIST', function(event, playlist) {
        var isAlreadyLoadedPlaylist = getIsPlaylistInList(playlist, $scope.openedPlaylists);

        if(isAlreadyLoadedPlaylist){
            $scope.setCurrentPlaylist(isAlreadyLoadedPlaylist);
        } else {
            var new_playlist = angular.copy(playlist);
            $scope.openedPlaylists.push(new_playlist);
            $scope.setCurrentPlaylist(new_playlist);
            $scope.$emit('LOAD_PLAYLIST_TRACKS', new_playlist);
        }
    });

    $scope.$on('LOAD_PLAYLIST_TRACKS', function(event, playlist){
        if(playlist.tracks == undefined){
            playlist.loading = true;
            Playlist.get({id: playlist.id}, function(playlist_data){
                playlist.loading = false;
                playlist.tracks = playlist_data.tracks;
                playlist.saved = true;
            });
        }
    });

    $scope.$on('ADD_FILE_TO_PLAYLIST', function(event, file){
        if(file.type == undefined){
            $scope.currentPlaylist.tracks.push($scope.trackFromFile(file));
        }
        else{
            $scope.currentPlaylist.tracks.push(file);
        }

        $scope.$emit('SET_SAVED_FALSE', $scope.currentPlaylist);

        if(($scope.currentPlaylist.tracks.length == 1) && $rootScope.autoPlay){
            $scope.playTrack();
        };
    });

    $scope.$on('SET_SAVED_FALSE', function(event, playlist){
        var isSavedPlaylist = getIsPlaylistInList(playlist, $scope.playlists);

        if(isSavedPlaylist){
            playlist.saved = false;
        };
    });

    $scope.closePlaylist = function(index){
        $scope.openedPlaylists.splice(index, 1);
        $scope.setCurrentPlaylist($scope.openedPlaylists[index - 1]);
    }

    $rootScope.loadingPlaylistbrowser = true;

    $scope.showPlaylists = function(){
        $scope.mediaBrowserMode = 'playlist';
    };

    $scope.trackFromFile = function(file){
        return {
            type: LOCAL_STORAGE,
            data: file,
        }
    };

    $scope.sortPlaylistBy = function(playlist, expression){
        $scope.currentPlaylist.tracks = $filter('orderBy')(playlist.tracks, function(track){
            return track.data[expression];
        });
    };

    $scope.uploadPlaylist = function(files, errFiles) {
        $scope.files = files;
        $scope.errFiles = errFiles;
        angular.forEach(files, function(file) {
            file.upload = Upload.upload({
                url: API_IMPORT_PLAYLIST_URL  + file.name,
                data: {file: file},
                method: 'PUT',
            });

            file.upload.then(function (response) {
                $timeout(function () {
                    var playlist = response.data.playlist;
                    if(playlist != undefined){
                        playlist.loading = false;
                        playlist.saved = true;
                        $scope.playlists.push(playlist);
                        $scope.addNotification('Added playlist: ' + response.data.playlist.name);
                    }                   
                });
            }, function (response) {
                $scope.addNotification('Error: ' + response.data);
            });
        });
    }

});
