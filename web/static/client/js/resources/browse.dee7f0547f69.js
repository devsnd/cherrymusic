app.factory('Browse', ['$http',
    function($http){
        Browse = {};
        Browse.get = function(path, success, error) {
            return $http.get(API_URL + 'browse/' + path, {cache: true})
                .success(function (data) {
                    success(data);
                })
                .error(function (data) {
                    error(data);
                });
        };
        return Browse
    }
]);
