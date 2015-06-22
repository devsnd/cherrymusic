app.directive('mediaPlayer', [
  function() {
      return {
          restrict: 'E',
          templateUrl: STATIC_FILES + 'client/templates/mediaplayer.html',
          scope: {
              playlists: '=',
              currentPlaylist: '='
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
                  $scope.currentPlaylist = playlist;
              };

              $scope.playTrack = function(trackNr){
                  $scope.currentTrackIndex = trackNr;
                  $scope.$emit('PLAY_TRACK', $scope.currentPlaylist, $scope.currentPlaylist.tracks[trackNr]);
              };

              $scope.savePlaylist = function(playlist){

              }
          }
      }
  }
]);
