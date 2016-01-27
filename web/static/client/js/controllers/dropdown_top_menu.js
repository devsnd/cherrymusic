
app.controller('DropdownTopMenuController', function($scope, $rootScope, $uibModal, $filter, djangoAuth, User) {

    var openOptionsModal = function(){
        var uibModalInstance = $uibModal.open({
            animation: true,
            templateUrl: STATIC_FILES + 'client/modals/user_options.html',
            scope: $scope,
            controller: function($scope, $uibModalInstance){
                $scope.downloadPlaylistURL = API_EXPORT_PLAYLIST_URL;
                $scope.close = function(){
                    $uibModalInstance.dismiss('cancel');
                };
                $scope.saveSettings = function(){
                    $scope.$emit('SAVE_SETTINGS');
                    $scope.close();
                }
            }
        });
    };

    var openAdminPanelModal = function(){
        var uibModalInstance = $uibModal.open({
            animation: true,
            templateUrl: STATIC_FILES + 'client/modals/admin_panel.html',
            scope: $scope,
            controller: function($scope, $rootScope, $uibModalInstance, User){
                User.query(function(userList){
                    $rootScope.userList  = userList;
                });
            
                $scope.close = function(){
                    $uibModalInstance.dismiss('cancel');
                }
                $scope.indexLibrary = function(path){
                    $scope.$emit('INDEX_DIRECTORY', path)
                    $scope.indexingStarted = true;
                };
                $scope.createUser = function(username, password, isSuperuser){
                    $scope.$emit('CREATE_USER', username, password, isSuperuser);
                    resetForm();
                };
                $scope.deleteUser = function(user){
                    $scope.$emit('DELETE_USER', user);
                }
                var resetForm = function(){
                    $scope.newUsername = null;
                    $scope.newPassword = null;
                    $scope.isSuperuser = false;
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
        }
        else if(selected.value == 'admin'){
            openAdminPanelModal();
        };

    };
});
