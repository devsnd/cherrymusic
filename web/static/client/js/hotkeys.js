
app.config(function(hotkeysProvider) {
        hotkeysProvider.includeCheatSheet = false;
    })

app.controller('HotkeysCtrl', function($scope, $rootScope, hotkeys) {
  // You can pass it an object.  This hotkey will not be unbound unless manually removed
  // using the hotkeys.del() method
  var volumeStep = 0.10;
  hotkeys.add({
        combo: $rootScope.increaseVolumeKey,
        description: 'Increase volume',
        callback: function() {
            if ($rootScope.volume < (1 - volumeStep)){
                $rootScope.volume += volumeStep;
            }
            else{
                $rootScope.volume = 1;
            }
            $scope.playback.volume($rootScope.volume);
        }
    });

  hotkeys.add({
        combo: $rootScope.decreaseVolumeKey,
        description: 'Decrease volume',
        callback: function() {
            if ($rootScope.volume > (volumeStep)){
                $rootScope.volume -= volumeStep;
            }
            else{
                $rootScope.volume = 0;
            }
            $scope.playback.volume($rootScope.volume);
        }
    });

    hotkeys.add({
        combo: $rootScope.toggleMuteKey,
        description: 'Mute/Unmute',
        callback: function() {
            if ($scope.isMute){
                $scope.unmute();
            }
            else{
                $scope.mute();
            };
        }
    });

    hotkeys.add({
        combo: $rootScope.previousTrackKey,
        description: 'Previous track',
        callback: function() {
            $scope.playPreviousTrack();
        }
    });

    hotkeys.add({
        combo: $rootScope.nextTrackKey,
        description: 'Next track',
        callback: function() {
            $scope.playNextTrack();
        }
    });

    hotkeys.add({
        combo: $rootScope.togglePlayKey,
        description: 'Play/Pause',
        callback: function() {
            console.log($rootScope.isPlaying);
            if ($rootScope.isPlaying){
                $scope.playback.pause();
            }
            else{
                $scope.playTrack();
            };
        }
    });


});