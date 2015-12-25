app.factory('ConfigService', function(LegacyAPIService, AuthService, $q){
    var config = {};
    var configLoaded = false;

    return {
        getHeartbeatIntervalSec: function(){
            return 60;
        },
        ready: function(){
            return configLoaded;
        },
        init: function(){
            var deferred = $q.defer();
            LegacyAPIService.post('api/getconfiguration').then(function(data){
                configLoaded = true;
                config = data;
                // insert auth specific data into the AuthService for now:
                AuthService.legacyInit(config.username, !!config.isadmin);
                deferred.resolve();
            }, function(){
                alert('Failed to load configuration from server. Please try again later.')
                deferred.reject();
            })
            return deferred.promise;
        },
        getDecoders: function(){
            return config.getdecoders;
        },
        getEncoders: function(){
            return config.getencoders;
        },
        albumArtFetchingEnabled: function(){
            return config.fetchalbumart;
        },
        autoLoginEnabled: function(){
            return config.auto_login;
        },
        getServePath: function(){
            return config.servepath;
        },
        getTranscodingPath: function(){
            return config.transcodepath;
        },
        getVersion: function(){
            return config.version;
        }
    }
});