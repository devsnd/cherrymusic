
app.config(function(hotkeysProvider) {
    hotkeysProvider.includeCheatSheet = false;
  })

app.controller('HotkeysCtrl', function($scope, hotkeys) {
  $scope.volume = 5;

  // You can pass it an object.  This hotkey will not be unbound unless manually removed
  // using the hotkeys.del() method
  hotkeys.add({
    combo: 'ctrl+up',
    description: 'This one goes to 11',
    callback: function() {
      $scope.volume += 1;
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