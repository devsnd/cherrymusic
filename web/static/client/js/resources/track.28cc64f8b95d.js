app.factory('Track', ['$resource',
    function($resource){
        return $resource(API_URL + 'track/:id');
    }
]);