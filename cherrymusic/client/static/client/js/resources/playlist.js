app.factory('Playlist', ['$resource',
    function($resource){
        return $resource(API_URL + 'playlist/:id/', null,
        {
            'update': { method:'PUT' }
        });
    }
]);

app.factory('PlaylistSearch', ['$http',
    function($http){
        PlaylistSearch = {};
        PlaylistSearch.get = function(query, success, error) {
            return $http.get(API_URL + 'playlist/?search=' + query, {cache: true})
                .success(function (data) {
                    success(data);
                })
                .error(function (data) {
                    error(data);
                });
        };
        return PlaylistSearch
    }
]);
