app.directive('playlistBrowser', ['$rootScope', 'UserList',
    function($rootScope, UserList) {
        return {
            restrict: 'E',
            templateUrl: STATIC_FILES + 'client/templates/playlistbrowser.html',
            scope: {
                playlists: '='
            },
            controller: function ($scope) {
                $scope.playlistSortBy = '-id';

                $scope.playlistSortBySomething = function(something){
                    console.log(something);
                    if($scope.playlistSortBy == something){
                        $scope.playlistSortBy = '-' + something
                    }
                    else{
                        $scope.playlistSortBy = something
                    };
                };
                
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
                    var l = 0.5
                    var f = (h * 6 - i)-l;
                    var q = 1 - f - l;
                    switch(i % 6){
                        case 0: r = l; g = q; b = 1; break; // pink - blue
                        case 1: r = f; g = l; b = 1; break; // pink - blue
                        case 2: r = l; g = 1; b = f; break; // green
                        case 3: r = 1; g = f; b = l; break; // pink
                        case 4: r = 1; g = l; b = q; break; // pink
                        case 5: r = q; g = 1; b = l; break; // yellow
                    }
                    var c = "#" + ("00" + (~ ~(r * 255)).toString(16)).slice(-2) + ("00" + (~ ~(g * 255)).toString(16)).slice(-2) + ("00" + (~ ~(b * 255)).toString(16)).slice(-2);
                    return (c);
                };

                $scope.addUserBackgroundColor = function(userId){
                    return {'background-color': rainbow($rootScope.userList.length*2+30, userId*2)}
                }
            }
        }
    }
]);
