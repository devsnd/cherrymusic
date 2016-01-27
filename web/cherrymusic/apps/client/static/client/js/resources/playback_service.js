app.factory('PlaybackService', ['$injector', '$rootScope', function($injector, $rootScope){
    var backend = null;

    assureBackend = function() {
        if (backend == null) {
            throw "No backend defined!"
        }
    };

    var currentTrack = null;

    return {
        setBackend: function(backendServiceName){
            backend = $injector.get(backendServiceName);
        },
        setTrack: function(track, start_time){
            currentTrack = track;
            backend.setTrack(track, start_time);
        },
        seek: function(start_time){
            backend.seek(start_time);
            $rootScope.isPlaying = true;
        },
        play: function(start_time){
            backend.play(start_time);
            $rootScope.isPlaying = true;
        },
        pause: function(start_time){
            backend.pause();
            $rootScope.isPlaying = false;
        },
        stop: function(){
            backend.stop();
            $rootScope.isPlaying = false;
            $rootScope.$emit('DELETE_CURRENT_TRACK');
        },
        currentTime: function(){
            return backend.currentTime();
        },
        totalTime: function(){
            return backend.totalTime();
        },
        volume: function(volume){
            return backend.volume(volume);
        },
        mute: function(){
            return backend.mute();
        },
        unmute: function(){
            return backend.unmute();
        },

    }
}]);