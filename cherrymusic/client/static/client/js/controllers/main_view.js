app.controller('MainViewController', function($scope, $rootScope, $uibModal, $controller, $window, Browse, IndexDirectory, djangoAuth, UserSettings){
    djangoAuth.authenticationStatus();

    $scope.userMayDownload = true;
    $scope.mediaBrowserMode = 'motd';

    var getSettings = function(){
        UserSettings.query(function(settings){
            $scope.userSettings = settings[0];

            $rootScope.increaseVolumeKey = $scope.userSettings.hotkeys.increase_volume;
            $rootScope.decreaseVolumeKey = $scope.userSettings.hotkeys.decrease_volume;
            $rootScope.toggleMuteKey = $scope.userSettings.hotkeys.toggle_mute;
            $rootScope.previousTrackKey = $scope.userSettings.hotkeys.previous_track;
            $rootScope.nextTrackKey = $scope.userSettings.hotkeys.next_track;
            $rootScope.togglePlayKey = $scope.userSettings.hotkeys.toggle_play;
            $rootScope.autoPlay = $scope.userSettings.misc.auto_play;
            $rootScope.confirmClosing = $scope.userSettings.misc.confirm_closing;
            $rootScope.showAlbumArt = $scope.userSettings.misc.show_album_art;
            $rootScope.removeWhenQueue = $scope.userSettings.misc.remove_when_queue; 

            angular.extend(this, $controller('HotkeysCtrl', {$scope: $scope}));
        });
    };

    getSettings();

    $scope.fileBrowserContent = {};

    angular.extend(this, $controller('JPlayerCtrl', {$scope: $scope}));
    angular.extend(this, $controller('PlaylistsCtrl', {$scope: $scope}));

    $scope.$on('SAVE_SETTINGS', function(event){
        var newSettings = $scope.userSettings;
        newSettings.hotkeys.increase_volume = $rootScope.increaseVolumeKey;
        newSettings.hotkeys.decrease_volume = $rootScope.decreaseVolumeKey;
        newSettings.hotkeys.toggle_mute = $rootScope.toggleMuteKey;
        newSettings.hotkeys.previous_track = $rootScope.previousTrackKey;
        newSettings.hotkeys.next_track = $rootScope.nextTrackKey;
        newSettings.hotkeys.toggle_play = $rootScope.togglePlayKey;
        newSettings.misc.auto_play = $rootScope.autoPlay;
        newSettings.misc.confirm_closing = $rootScope.confirmClosing;
        newSettings.misc.show_album_art = $rootScope.showAlbumArt;
        newSettings.misc.remove_when_queue = $rootScope.removeWhenQueue;

        console.log(newSettings);
        
        UserSettings.update({ id:$scope.userSettings.user}, newSettings, function(){
            console.log('Settings updated');
        });
    });


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
