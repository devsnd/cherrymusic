app.factory('Playlist', ['$resource',
    function($resource){
        return $resource(API_URL + 'playlist/:id', {id: '@id'});
    }
]);

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

app.factory('IndexDirectory', ['$http',
    function($http){
        IndexDirectory = {};
        IndexDirectory.index = function(path, success, error) {
            return $http.get(API_URL + 'index/' + path)
                .success(function (data) {
                    if(success !== undefined){
                        success(data);
                    }
                })
                .error(function (data) {
                    if(error !== undefined) {
                        error(data);
                    }
                });
        };
        return IndexDirectory
    }
]);