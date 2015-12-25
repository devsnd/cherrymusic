app.factory('UserOptionService', function($resource, $http, $q){
    var options = {};
    var optionsLoaded = false;
    var userOptionResource = $resource(
        'api/getuseroptions'
    );

    var traverseSetOption = function(traversePath, value){
        // takes an option `traversePath` string like "misc.some.option" and  
        // applies the value to `UserOptionService.options.misc.some.option`

        var pathElements = traversePath.split('.');
        var parent = options;
        // traverse through to the second to last object
        for(var i=0; i<pathElements.length - 1; i++){
            parent = parent[pathElements[i]];
        }
        // assign directly to seconds to last object in tree to retain reference
        parent[pathElements[pathElements.length - 1]] = value
    }

    return {
        getAll: function(){
            return options;
        },
        get: function(key){

        },
        set: function(keypath, value){
            var deferred = $q.defer();
            $http({
                method: 'POST',
                url: 'api/setuseroption',
                data: 'data='+encodeURIComponent(JSON.stringify({
                    "optionkey": keypath,
                    "optionval": value
                })),
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            }).then(function(){
                traverseSetOption(keypath, value);
                deferred.resolve();
            }, function(){
                deferred.reject();
            });
            return deferred.promise;
        },
        init: function(){
            userOptionResource.get({},
                function(data){
                    options = data.data;
                    optionsLoaded = true;
                },
                function(data){
                    console.log('Error loading user options!');
                }
            );
        }
    }
});