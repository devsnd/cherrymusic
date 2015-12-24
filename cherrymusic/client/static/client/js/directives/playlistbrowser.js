app.directive('playlistBrowser', [
  function() {
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
              }
              $scope.addAllTracksToPlaylist = function(tracks){
                  tracks.forEach(function(track){
                      $scope.addToPlaylist(track);
                  });
              };
          }
      }
  }
]);
