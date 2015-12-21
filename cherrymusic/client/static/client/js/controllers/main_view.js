app.controller('MainViewController', function($scope, $rootScope, $uibModal, $controller, Browse, IndexDirectory, djangoAuth){
    djangoAuth.authenticationStatus();

    angular.extend(this, $controller('HotkeysCtrl', {$scope: $scope}));
    angular.extend(this, $controller('JPlayerCtrl', {$scope: $scope}));
    angular.extend(this, $controller('PlaylistsCtrl', {$scope: $scope}));

    $scope.openAboutModal = function(){
        var uibModalInstance = $uibModal.open({
            animation: true,
            templateUrl: STATIC_FILES + 'client/modals/about.html',
            controller: function($scope, $uibModalInstance){
                $scope.close = function(){
                    $uibModalInstance.dismiss('cancel');
                }
            }
        });
    };

    $scope.openChangePasswordModal = function(){
        var uibModalInstance = $uibModal.open({
            animation: true,
            templateUrl: STATIC_FILES + 'client/modals/change_password.html',
            scope: $scope,
            controller: function($scope, $uibModalInstance){
                $scope.close = function(){
                    $uibModalInstance.dismiss('cancel');
                }
            }
        });
    };

    $scope.userMayDownload = true;
    $scope.mediaBrowserMode = 'motd';

    $scope.fileBrowserContent = {};

    $scope.browse = function(directory){
        Browse.get(directory, function(data){
            $scope.fileBrowserContent = data
        });
        $scope.mediaBrowserMode = 'file'
    };

    $scope.$on('INDEX_DIRECTORY', function(event, path){
        IndexDirectory.index(path);
    });

    $scope.$on('LOAD_DIRECTORY', function(event, directory){
       $scope.browse(directory);
    });

    $scope.albumArtUrl = function(filepath){
        return API_URL + 'albumart/' + filepath
    };
});
