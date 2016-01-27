app.directive('playlistBrowser', ['$rootScope', 'PlaylistSearch',
    function($rootScope, PlaylistSearch) {
        return {
            restrict: 'E',
            templateUrl: STATIC_FILES + 'client/templates/playlistbrowser.html',
            scope: {
                playlists: '='
            },
            controller: function ($scope) {
                $scope.playlistSortBy = '-id';

                $scope.playlistSortBySomething = function(something){
                    if($scope.playlistSortBy == something){
                        $scope.playlistSortBy = '-' + something
                    }
                    else{
                        $scope.playlistSortBy = something
                    };
                };

                $scope.playlistSearch = function(query){
                    PlaylistSearch.get(query, function(data){
                        $scope.playlists = data;
                    });
                };
                
                $scope.loadPlaylist = function(playlist){
                    $scope.$emit('LOAD_PLAYLIST', playlist);
                };

                $scope.loadPlaylistTracks= function(playlist){
                    $scope.$emit('LOAD_PLAYLIST_TRACKS', playlist);
                };
                
                $scope.removePlaylist = function(playlist){
                    $scope.$emit('REMOVE_PLAYLIST', playlist);
                };

                $scope.updatePlaylist = function(playlist){
                    $scope.$emit('UPDATE_PLAYLIST', playlist);
                };

                $scope.addToPlaylist = function(track){
                    $scope.$emit('ADD_FILE_TO_PLAYLIST', track);
                };

                $scope.addAllTracksToPlaylist = function(tracks){
                    tracks.forEach(function(track){
                        $scope.addToPlaylist(track);
                    });
                };
            }
        }
    }
]);
