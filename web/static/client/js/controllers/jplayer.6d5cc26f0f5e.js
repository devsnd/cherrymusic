app.controller('JPlayerCtrl', function($scope, $rootScope, PlaybackService) {
    $scope.isMute = false;
    $rootScope.isPlaying = false;
    $rootScope.volume = 1;

    var getTitle = function(track){
        var defaultTitle = 'CherryMusic';
        if(track == undefined){
            return defaultTitle;
        }
        else if(track.data.meta_title){
            return track.data.meta_track + ' ' + track.data.meta_artist +
                ' - ' + track.data.meta_title + ' | ' + defaultTitle;
        }
        else{
            return track.data.filename + ' | ' + defaultTitle;
        };
    };

    $rootScope.title = getTitle(null);
    PlaybackService.setBackend('PlaybackServiceJPlayer');
    $scope.playback = PlaybackService;

    $scope.$on('JUMP_TO_UNIT', function(event, unit){
        PlaybackService.seek(PlaybackService.totalTime() * unit);
    });

    $scope.$on('VOLUME_TO_UNIT', function(event, unit){
        $rootScope.volume = unit;
        $scope.playback.volume($rootScope.volume);
    });

    $rootScope.$on('DELETE_CURRENT_TRACK', function(event){
        $scope.currentPlayingTrack = null;
        $rootScope.title = getTitle(null);
    });

    $scope.mute = function(){
        $scope.playback.mute();
        $scope.isMute = true;
    };

    $scope.unmute = function(){
        $scope.playback.unmute();
        $scope.isMute = false;
    };

    $scope.maxVolume = function(){
        $rootScope.volume = 1;
        $scope.playback.volume($rootScope.volume);
    }

    $scope.currentPlaybackPercentage = 0;

    $rootScope.$on('PLAYBACK_TIME_UPDATE', function(event, currentTime, totalTime){
        // PlaybackService gives correct totalTime always from metada, totalTime comes from JPlayer and sometimes fail
        totalTime = PlaybackService.totalTime();

        $scope.currentPlayTime = currentTime;

        $scope.currentPlaybackPercentage = currentTime / totalTime * 100;
        if(!$scope.$$phase) {
            $scope.$digest(); // HACK: force progress bar update
        }

        var remainingTrackTime = totalTime - currentTime;

        $scope.updateRemainingPlaylistPercentage(remainingTrackTime)
    });
    $rootScope.$on('PLAYBACK_ENDED', function(){
        $scope.playNextTrack();
        console.log('Playback end');
    });

    $scope.startPlaylingTrack = function(index){
        $scope.currentPlayingPlaylist = $scope.currentPlaylist;
        $scope.playTrack(index);
    }

    $scope.playTrack = function(index){
        var starTime = 0;
        var track = null;

        if(index == undefined){
            if($scope.currentPlayingTrack){
                starTime = $scope.currentPlayTime;
                track = $scope.currentPlayingTrack;
            }
            else{
                track = trackFromIndex(0);
                $scope.currentTrackIndex = 0;
            };   
        }
        else{
            $scope.currentTrackIndex = index;
            track = trackFromIndex(index);
        };
        $scope.currentPlayingTrack = track;

        $rootScope.title = getTitle(track);

        if(track.type == LOCAL_STORAGE){
            PlaybackService.setTrack(track, starTime);
            PlaybackService.play();
        } else {
            console.error('Cannot play track of type '+track.type);
        }
    };

    var trackFromIndex = function(index){
        return $scope.currentPlayingPlaylist.tracks[index];
    };

    $scope.playNextTrack = function(){
        var nextIndex = getNextIndex();
        if(nextIndex == null){
            $scope.playback.stop()
        }
        else{
            $scope.playTrack(nextIndex);
        };
    };

    var getNextIndex = function(){
        var currentIndex = $scope.currentTrackIndex;
        var tracksInPlaylist = $scope.currentPlayingPlaylist.tracks.length;

        if($scope.currentPlayingPlaylist.type == 'queue' && $rootScope.removeWhenQueue){
            if($scope.currentPlayingPlaylist.tracks[currentIndex] == $scope.currentPlayingTrack){
                $scope.currentPlayingPlaylist.tracks.splice(currentIndex, 1);
            };
            return (tracksInPlaylist > 1) ? 0 : null;
        };

        $scope.indexHistory.push(currentIndex);

        var followedIndex = ((currentIndex + 1) < tracksInPlaylist) ? currentIndex + 1 : 0;

        if($scope.isShuffle){
            return Math.round(Math.random() * (tracksInPlaylist - 1));
        };

        if(!$scope.isRepeat && followedIndex == 0 ){
            $scope.currentTrackIndex = null;
            $scope.currentPlayingTrack = null;
            return null;
        };
        return (followedIndex);
    };

    $scope.playPreviousTrack = function(){
        var previousIndex = getPreviousIndex();
        if(previousIndex == null){
            $scope.playback.stop()
        }
        else{
            $scope.playTrack(previousIndex);
        };
    };

    var getPreviousIndex = function(){
        var currentIndex = $scope.currentTrackIndex;
        var followedIndex = ((currentIndex - 1) >= 0) ? currentIndex - 1 : null;
        var historyLength = $scope.indexHistory.length;

        if($scope.isShuffle && historyLength >= 1){
            var lastPlayed = historyLength - 1;
            followedIndex = $scope.indexHistory[lastPlayed];
            $scope.indexHistory.splice(lastPlayed, 1);
        };  

        return followedIndex;
    };
});