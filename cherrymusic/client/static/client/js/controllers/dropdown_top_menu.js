
app.controller('DropdownTopMenuController', function($scope, $rootScope, $uibModal, djangoAuth, User) {

    var openOptionsModal = function(){
        var uibModalInstance = $uibModal.open({
            animation: true,
            templateUrl: STATIC_FILES + 'client/modals/user_options.html',
            scope: $scope,
            controller: function($scope, $uibModalInstance){
                $scope.close = function(){
                    $uibModalInstance.dismiss('cancel');
                }
            }
        });
    };
    $scope.ddTopMenu = {};

    $scope.ddSelectTopMenu = {};

    $scope.updateDdTopMenu = function() {
        $scope.ddTopMenu = getDdTopMenu();
    };

    var getDdTopMenu = function()
    {
        var menuOptions = [
            {
                text: 'Options',
                value: 'options',
            },
            {
                divider: true
            },
            {
                text: 'Logout (' + $rootScope.user.username + ')',
                value: 'logout'
            }
        ];
        if($rootScope.user.is_superuser){
            menuOptions.splice(1, 0,{
                text: 'Admin',
                value: 'admin',
                href: ADMIN_URL,
            });
        }

        return menuOptions;
    };

    $scope.ddLauncher = function(selected){
        if(selected.value == 'options'){
            openOptionsModal();
        }
        else if(selected.value == 'logout'){
            djangoAuth.logout();
            window.location.replace(LOGIN_URL);
        };

    };
});
