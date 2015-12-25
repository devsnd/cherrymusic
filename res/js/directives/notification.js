app.directive('cmNotification', function() {
  return {
    scope: {
      notification: '=',
    },
    template: '<div \
        class="alert alert-dismissable" \
        ng-class="{ \
            \'alert-info\': notification.type==\'info\', \
            \'alert-danger\': notification.type==\'error\', \
            \'alert-success\': notification.type==\'success\', \
        }"> \
            <button class="close" ng-click="dismiss(notification)"> \
                &times; \
            </button> \
            {{ notification.message }} \
        </div> \
    ',
    controller: function($scope, NotificationService){
        $scope.dismiss = function(){
            NotificationService.dismiss($scope.notification);
        }
    }
  }
});
