app.directive('mediaPlayer', [
    'Track',
  function(Track) {
      return {
          restrict: 'E',
          templateUrl: STATIC_FILES + 'client/templates/mediaplayer.html',
          scope: {
              playlists: '=',
              currentPlaylist: '=',
              currentTrackIndex: '=',
              playTrack: '=',
              indexHistory: '='
          },
          controller: function ($scope) {
              $scope.currentTrackIndex = 0;

              $scope.createNewPlaylist = function(){
                  $scope.$emit('CREATE_NEW_PLAYLIST');
              };

              $scope.savePlaylist = function(playlist){
                  console.log(playlist)
              };

              $scope.clearPlaylist = function(playlist){
                playlist.tracks = [];
              };

              $scope.setCurrentPlaylist = function(playlist){
                  console.log(playlist);
                  $scope.currentPlaylist = playlist;
                  $scope.indexHistory = [];
              };

              $scope.savePlaylist = function(playlist){
                console.log('savePlaylist is a STUB.');
              };

              $scope.dropCallback = function(event, index, item){
                  if(item.type === undefined){
                    return Track.fromFile(item);
                  }
                  return item;
              };
          }
      }
  }
]);
