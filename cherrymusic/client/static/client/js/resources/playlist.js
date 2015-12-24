app.factory('Playlist', ['$resource',
    function($resource){
        return $resource(API_URL + 'playlist/:id/', null,
        {
            'update': { method:'PUT' }
        });
    }
]);