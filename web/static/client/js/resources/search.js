app.factory('Search', ['$http',
    function($http){
        Search = {};
        Search.get = function(query, success, error) {
            return $http.get(API_URL + 'search/?q=' + query, {cache: true})
                .success(function (data) {
                    success(data);
                })
                .error(function (data) {
                    error(data);
                });
        };
        return Search
    }
]);
