app.directive('playlistBrowser', ['$rootScope', 'UserList',
    function($rootScope, UserList) {
        return {
            restrict: 'E',
            templateUrl: STATIC_FILES + 'client/templates/playlistbrowser.html',
            scope: {
                playlists: '='
            },
            controller: function ($scope) {
                $scope.loadPlaylist = function(playlist){
                    $scope.$emit('LOAD_PLAYLIST', playlist);
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

                var rainbow = function(numOfSteps, step) {
                    var r, g, b;
                    var h = step / numOfSteps;
                    var i = ~~(h * 6);
                    var f = h * 6 - i;
                    var q = 1 - f;
                    switch(i % 6){
                        case 0: r = 1; g = f; b = 0; break;
                        case 1: r = q; g = 1; b = 0; break;
                        case 2: r = 0; g = 1; b = f; break;
                        case 3: r = 0; g = q; b = 1; break;
                        case 4: r = f; g = 0; b = 1; break;
                        case 5: r = 1; g = 0; b = q; break;
                    }
                    var c = "#" + ("00" + (~ ~(r * 255)).toString(16)).slice(-2) + ("00" + (~ ~(g * 255)).toString(16)).slice(-2) + ("00" + (~ ~(b * 255)).toString(16)).slice(-2);
                    return (c);
                };

                $scope.addUserBackgroundColor = function(userId){
                    return {'background-color': rainbow($rootScope.userList.length, userId)}
                }
            }
        }
    }
]);
