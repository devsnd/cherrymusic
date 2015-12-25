app.directive('cmMessageOfTheDay', function(MOTDService) {
  return {
    template: " \
    <div ng-if=\"type == 'wisdom'\"> \
        useless wisdom<hr>{{ wisdom }} \
    </div> \
    <div ng-if=\"type == 'update'\"> \
        TODO: MESSAGE OF THE DAY UPDATE! \
    </div> \
    ",
    controller: function($scope){
        MOTDService.fetch().then(function(data){
            $scope.type = data.type;
            if($scope.type == 'wisdom'){
                $scope.wisdom = data.data;
            } else if($scope.type == 'update'){
                //TODO update rendering is not finished.
                alert('TODO: motd type update');
            } else {
                console.log('Cannot render motd type '+data.type);
            }
        })
    }
  }
});
