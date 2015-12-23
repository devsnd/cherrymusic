app.controller('MainViewController', function($scope, $rootScope, $uibModal, $controller, $window, Browse, IndexDirectory, djangoAuth){
    djangoAuth.authenticationStatus();

    $scope.userMayDownload = true;
    $scope.mediaBrowserMode = 'motd';

    //TODO: save in user options
    $rootScope.autoPlay = false;
    $rootScope.confirmClosing = true;
    $rootScope.showAlbumArt = true;
    $rootScope.increaseVolumeKey = 'ctrl+up';
    $rootScope.decreaseVolumeKey = 'ctrl+down';
    $rootScope.toggleMuteKey = 'ctrl+m';
    $rootScope.previousTrackKey = 'ctrl+left';
    $rootScope.nextTrackKey = 'ctrl+right';
    $rootScope.togglePlayKey = 'space'; 

    $scope.fileBrowserContent = {};

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

    $window.onbeforeunload = function( event ) {
        if($rootScope.isPlaying && $rootScope.confirmClosing){
            var answer = confirm("Are you sure you want to leave this page?")
            if (!answer) {
                event.preventDefault();
            };
        };
    };

    $rootScope.changeKey = 'change';
    $rootScope.updateKey = function(event, key){
        console.log($rootScope[key]);
        $rootScope[key] = event.key;
        $rootScope.changeKey = 'change';
    }
});
