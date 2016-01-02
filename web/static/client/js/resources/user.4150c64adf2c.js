app.factory('User', ['$resource',
    function($resource){
        return $resource(API_URL + 'user/:id/', null);
    }
]);