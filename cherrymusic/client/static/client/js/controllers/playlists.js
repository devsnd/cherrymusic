app.controller('PlaylistsCtrl', function($scope, $rootScope, Playlist, Track) {

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
        $scope.currentPlaylist.tracks.push(Track.fromFile(file));
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

    $scope.$on('CREATE_NEW_PLAYLIST', function(event){
        var newPlaylist = createEmptyPlaylist('New Playlist', 'playlist');
        $scope.openedPlaylists.push(newPlaylist);
        $scope.currentPlaylist = newPlaylist;
        $scope.indexHistory = [];
    });
});