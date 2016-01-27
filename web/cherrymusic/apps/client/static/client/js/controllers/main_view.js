app.controller('MainViewController', function($scope, $rootScope, $uibModal, $controller, $window,
     Browse, Search, IndexDirectory, djangoAuth, User, UserSettings, Directory){
    djangoAuth.authenticationStatus();

    $rootScope.loadingFilebrowser = true;

    var updateDirectoryList = function(){
        Directory.query(function(directoryList){
            $scope.directoryList = directoryList;
            $rootScope.loadingFilebrowser = false;
        });
    };

    updateDirectoryList();

    $scope.userMayDownload = false;
    $scope.mediaBrowserMode = 'motd';

    User.query(function(userList){
        $rootScope.userList  = userList;
    });

    var getSettings = function(){
        UserSettings.query(function(settings){
            $scope.userSettings = settings[0];

            User.get({id: $scope.userSettings.user}, function(user){
                $rootScope.user = user;
            });

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

    $scope.search = function(query){
        Search.get(query, function(data){
            $scope.fileBrowserContent = data
        });
        $scope.mediaBrowserMode = 'file'
    };

    $scope.$on('INDEX_DIRECTORY', function(event, path){
        IndexDirectory.index(path);
        updateDirectoryList();
    });

    $scope.$on('LOAD_DIRECTORY', function(event, directory){
        if(directory.parent === undefined){
            $scope.browse(directory);            
        }
        else{
            var absolutePath = getAbsolutePath(directory);
            $scope.browse(absolutePath);
        }
    });

    var getAbsolutePath = function(directory, absolutePath){
        if(absolutePath == undefined){
            var absolutePath = [];
        }
        if(directory.parent != null){
            absolutePath.unshift(directory.path);        
            directory = getParentDirectory(directory);
            return getAbsolutePath(directory, absolutePath);
        }
        return absolutePath.join('/');
    };

    var getParentDirectory = function(directory){
        var parentId = directory.parent;
        return _.find($scope.directoryList, function(directory){ return directory.id == parentId });
    };

    $scope.$on('CREATE_USER', function(event, username, password, isSuperuser){
        var user = new User();
        user.username = username;
        user.password = password;
        user.is_superuser = isSuperuser;
        user.$save(user, function(user){
            User.query(function(userList){
                    $rootScope.userList  = userList;
                });
        }).then(function(response){
            $scope.addNotification('Successfully created user: ' + response.username);
        }, function(response){
            $scope.addNotification('Failed to create user.');
        });
    });

    $scope.$on('DELETE_USER', function(event, user){
        var answer = confirm("Are you sure you want to delete this user?")
        if (!answer) {
            return;
        };
        User.remove({id:user.id}, function(){
            User.query(function(userList){
                    $rootScope.userList  = userList;
                });
        });
    });

    $scope.albumArtUrl = function(filepath){
        return API_ALBUMART_URL + filepath
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

    var rainbow = function(numOfSteps, step) {
        var r, g, b;
        var h = step / numOfSteps;
        var i = ~~(h * 6);
        var l = 0.5
        var f = (h * 6 - i)-l;
        var q = 1 - f - l;
        switch(i % 6){
            case 0: r = l; g = q; b = 1; break; // pink - blue
            case 1: r = f; g = l; b = 1; break; // pink - blue
            case 2: r = l; g = 1; b = f; break; // green
            case 3: r = 1; g = f; b = l; break; // pink
            case 4: r = 1; g = l; b = q; break; // pink
            case 5: r = q; g = 1; b = l; break; // yellow
        }
        var c = "#" + ("00" + (~ ~(r * 255)).toString(16)).slice(-2) + ("00" + (~ ~(g * 255)).toString(16)).slice(-2) + ("00" + (~ ~(b * 255)).toString(16)).slice(-2);
        return (c);
    };

    $rootScope.addUserBackgroundColor = function(userId){
        return {'background-color': rainbow($rootScope.userList.length*2+30, userId*2)}
    }

    $scope.notifications = [];

    $scope.addNotification = function(notification){
      $scope.notifications.push(notification);
    };

});
