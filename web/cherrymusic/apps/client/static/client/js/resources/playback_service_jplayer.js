app.factory('PlaybackServiceJPlayer', ['$log', '$rootScope', function($log, $rootScope){
    // hacky: inject a hidden div into the HTML where the jplayer then can live
    var jplayerHTMLElem = $('<div id="jplayer-instance">');
    $('body').append(jplayerHTMLElem);

    var jplayerInstance = null;
    var currentTimeOffset = 0;
    var currentTime = 0;
    var totalTime = 0;
    var currentTrack = null;

    $("#jplayer-instance").jPlayer({
        ready: function () {
            jplayerInstance = $(this);
        },

        //cssSelectorAncestor: "#jp_container_1",
        swfPath: STATIC_FILES+"/client/bower_components/jPlayer/dist/jplayer/jquery.jplayer.swf",
        supplied: "oga",
        useStateClassSkin: true,
        autoBlur: false,
        smoothPlayBar: true,
        keyEnabled: true,
        remainingDuration: true,
        toggleDuration: true
    }).bind($.jPlayer.event.ended, function(){
        $rootScope.$emit('PLAYBACK_ENDED')
    }).bind($.jPlayer.event.timeupdate, function(event){
        currentTime = event.jPlayer.status.currentTime;
        totalTime = event.jPlayer.status.duration;
        $rootScope.$emit('PLAYBACK_TIME_UPDATE', currentTime, totalTime);
    });

    var setTrack = function(track, start_time){
        currentTimeOffset = start_time;

        if(track.type == LOCAL_STORAGE){
            currentTrack = track;
            var trackurl = API_STREAM_URL + track.data.path;
            if(start_time !== undefined){
                trackurl += '?start_time=' + start_time;
            }
            console.log('jPlayer: set track url: "'+trackurl+'"');
            jplayerInstance.jPlayer('setMedia', {
                'oga': trackurl});
        } else {
            $log.error('Cannot play track of type '+track.type);
        }
    };

    var play = function(start_time){
        if(start_time === 0){
            jplayerInstance.jPlayer('play');
        }
        else{
            console.log(start_time);
            jplayerInstance.jPlayer('play', start_time);
        }
    };

    return {
        play: play,
        seek: function(start_time){
            setTrack(currentTrack);
            play(start_time);
        },
        setTrack: setTrack,
        stop: function(){
            currentTimeOffset = 0;
            jplayerInstance.jPlayer('pause', 0);
        },
        pause: function(start_time){
            jplayerInstance.jPlayer('pause');
        },
        currentTime: function(){
            return currentTime + currentTimeOffset;
        },
        totalTime: function(){
            if(currentTrack != null && currentTrack.data.meta_duration){
                return currentTrack.data.meta_duration;
            }
            return totalTime;
        },
        volume: function(volume){
            jplayerInstance.jPlayer('volume', volume);
        },
        mute: function(){
            jplayerInstance.jPlayer('mute', true);
        },
        unmute: function(){
            jplayerInstance.jPlayer('mute', false);
        }
    };
}]);