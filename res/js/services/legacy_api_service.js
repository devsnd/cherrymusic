app.factory('LegacyAPIService', function($http, $q){
    return {
        post: function(endpoint, data){
            data = data || {};
            var deferred = $q.defer();
            $http({
                method: 'POST',
                url: endpoint,
                data: 'data='+encodeURIComponent(JSON.stringify(data)),
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            }).then(function(resp){
                deferred.resolve(resp.data.data);
            }, function(){
                deferred.reject();
            });
            return deferred.promise;
        }
    }
})