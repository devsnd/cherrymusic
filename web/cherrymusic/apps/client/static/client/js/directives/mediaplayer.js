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
  
                $scope.shuffle = function(array) {
                    var currentIndex = array.length, temporaryValue, randomIndex;
                  
                    // While there remain elements to shuffle...
                    while (0 !== currentIndex) {
                  
                        // Pick a remaining element...
                        randomIndex = Math.floor(Math.random() * currentIndex);
                        currentIndex -= 1;
                        // And swap it with the current element.
                        temporaryValue = array[currentIndex];
                        array[currentIndex] = array[randomIndex];
                        array[randomIndex] = temporaryValue;
                    }
                    return array;
                };

                $scope.removePlaylist = function(playlist){
                    $scope.$emit('REMOVE_PLAYLIST', playlist);
                };
            }
        }
    }
]);
