app.controller('PlaylistsCtrl', function($scope, $rootScope, $uibModal, Playlist, Track) {

    $scope.openSavePlaylistModal = function(){
        var uibModalInstance = $uibModal.open({
            animation: true,
            templateUrl: STATIC_FILES + 'client/modals/save_playlist.html',
            scope: $scope,
            controller: function($scope, $uibModalInstance){
                $scope.isPublic = false;

                $scope.close = function(){
                    $uibModalInstance.dismiss('cancel');
                };

                $scope.savePlaylist = function(playlist, title, isPublic){
                    $scope.$emit('SAVE_PLAYLIST', playlist, title, isPublic); 
                    $scope.close();
                } 
            }
        });
    };

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

    $scope.getRemainingTimeOrTracks = function (playlist) {
        return playlist.tracks.length;
    };
    $scope.getTotalTimeOrTracks = function (playlist) {
        return playlist.tracks.length;
    };

    $scope.getRemaingingPercentage = function (playlist) {
        return $scope.getRemainingTimeOrTracks(playlist) / $scope.getTotalTimeOrTracks(playlist) * 100
    };

    var createEmptyPlaylist = function(name, type){
        return {tracks: [], name: name, type: type};
    };

    var defaultPlaylist = createEmptyPlaylist('Queue', 'queue')
    $scope.playlists = [];
    $scope.openedPlaylists = [defaultPlaylist];
    $scope.currentPlaylist = defaultPlaylist;
    $scope.indexHistory = [];


    $scope.createNewPlaylist = function(){
        var newPlaylist = createEmptyPlaylist('New Playlist', 'playlist');
        $scope.openedPlaylists.push(newPlaylist);
        $scope.setCurrentPlaylist(newPlaylist);
        $scope.indexHistory = [];
    };

    $scope.clearPlaylist = function(playlist){
        playlist.tracks = [];
    };

    $scope.setCurrentPlaylist = function(playlist){
        $scope.currentTrackIndex = 0;
        $scope.currentPlaylist = playlist;
        $scope.indexHistory = [];
    };

    $scope.$on('SAVE_PLAYLIST', function(event, playlist, title, isPublic){
        var newPlaylist = new Playlist();
        newPlaylist.name = title;
        newPlaylist.owner = $rootScope.user.id;
        newPlaylist.public = isPublic;

        Playlist.save(newPlaylist, function(playlist){
            for(var order = 0, len = $scope.currentPlaylist.tracks.length; order < len; order++){
                var track = $scope.currentPlaylist.tracks[order];
                var newTrack = new Track();
                newTrack.playlist = playlist.id;
                newTrack.order = order;
                newTrack.type = track.type;
                newTrack.file = track.data.id;
                Track.save(newTrack, function(){});
            };
        });
    });

    $scope.$on ('REMOVE_PLAYLIST', function(event, playlist){
        var answer = confirm("Are you sure you want to remove this playlist?")
        if (!answer) {
            return;
        };

        Playlist.remove(playlist, function(){
            $scope.showPlaylists();
        });
    });

    $scope.$on('UPDATE_PLAYLIST', function(event, playlist){
        Playlist.update(playlist, function(){
            $scope.showPlaylists();
        });
    });

    $scope.$on('LOAD_PLAYLIST', function(event, playlist) {
        playlistid = playlist.id;
        var alreadyLoadedPlaylist = _.find(
            $scope.openedPlaylists,
            function(playlist){ return playlist.id == playlistid }
        );
        if(alreadyLoadedPlaylist){
            $scope.currentPlaylist = alreadyLoadedPlaylist;
        } else {
            playlist.loading = true;
            $scope.openedPlaylists.push(playlist);
            $scope.currentPlaylist = playlist;
            Playlist.get({id: playlistid}, function(playlist_data){
                playlist.loading = false;
                playlist.tracks = playlist_data.tracks;
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
        if(($scope.currentPlaylist.tracks.length == 1) && $rootScope.autoPlay){
            $scope.playTrack();
        };
    });

    $scope.showPlaylists = function(){
        $scope.mediaBrowserMode = 'playlist';
        Playlist.query(function(playlists){
            $scope.playlists = playlists;
        })
    };

    $scope.trackFromFile = function(file){
        return {
            type: LOCAL_STORAGE,
            data: file,
        }
    };
});
