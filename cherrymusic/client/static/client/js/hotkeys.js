
app.config(function(hotkeysProvider) {
        hotkeysProvider.includeCheatSheet = false;
    })

app.controller('HotkeysCtrl', function($scope, $rootScope, hotkeys) {
  // You can pass it an object.  This hotkey will not be unbound unless manually removed
  // using the hotkeys.del() method
  var volumeStep = 0.10;
  hotkeys.add({
        combo: 'ctrl+up',
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
        combo: 'ctrl+down',
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
        combo: 'ctrl+m',
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

    // when you bind it to the controller's scope, it will automatically unbind
    // the hotkey when the scope is destroyed (due to ng-if or something that changes the DOM)
    hotkeys.bindTo($scope)
        .add({
            combo: 'w',
            description: 'blah blah',
            callback: function() {}
        })
      // you can chain these methods for ease of use:

});