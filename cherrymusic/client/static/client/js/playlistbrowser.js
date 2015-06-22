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
          }
      }
  }
]);
