
app.controller('ChangePasswordController', function($scope, djangoAuth) {
    $scope.changePassword = function(oldpassword, newpassword, repeatnewpassword){

        console.log(oldpassword);
        djangoAuth.changePassword(newpassword, repeatnewpassword, oldpassword);


        $scope.oldpassword = null;
        $scope.newpassword = null;
        $scope.repeatnewpassword = null;
        $scope.changePasswordForm.$setPristine();
    };

});
