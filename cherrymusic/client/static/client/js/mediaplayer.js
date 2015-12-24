app.directive('mediaPlayer', [
  function() {
      return {
          restrict: 'E',
          templateUrl: STATIC_FILES + 'client/templates/mediaplayer.html',
          scope: true,
          controller: function ($scope) {
              $scope.dropCallback = function(event, index, item){
                  if(item.type === undefined){
                    return $scope.trackFromFile(item);
                  }
                  return item;
              };
          }
      }
  }
]);
