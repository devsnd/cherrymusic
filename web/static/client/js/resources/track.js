app.factory('Track', ['$resource',
    function($resource){
        return $resource(API_TRACK_URL + '/:id');
    }
]);