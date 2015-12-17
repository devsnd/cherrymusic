app.directive('playlistTab', function() {
    return {
        restrict: 'E',
        templateUrl: STATIC_FILES + 'client/templates/playlist.html',
        scope: {
            playlist:"=",
            onRemove:"&"
        },
        replace: true
    }
  })