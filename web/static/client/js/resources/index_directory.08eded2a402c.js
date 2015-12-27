
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