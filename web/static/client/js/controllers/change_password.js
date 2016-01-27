
app.controller('ChangePasswordController', function($scope, djangoAuth) {
    $scope.changePassword = function(oldpassword, newpassword, repeatnewpassword){

        djangoAuth.changePassword(newpassword, repeatnewpassword, oldpassword)
            .then(function(response){
                $scope.addNotification('Successfully password changed');
            }, function(response){
                $scope.addNotification('Failed to change password');
            });

        $scope.oldpassword = null;
        $scope.newpassword = null;
        $scope.repeatnewpassword = null;
        $scope.changePasswordForm.$setPristine();
    };

});
