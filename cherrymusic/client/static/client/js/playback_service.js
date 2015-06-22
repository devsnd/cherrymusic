app.factory('PlaybackService', ['$injector', function($injector){
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
        setTrack: function(track){
            currentTrack = track;
            backend.setTrack(track);
        },
        seek: function(start_time){
            backend.seek(start_time);
        },
        play: function(start_time){
            backend.play(start_time);
        },
        pause: function(start_time){
            backend.pause();
        },
        stop: function(){
            backend.stop();
        },
        currentTime: function(){
            return backend.currentTime();
        },
        totalTime: function(){
            return backend.totalTime();
        }
    }
}]);