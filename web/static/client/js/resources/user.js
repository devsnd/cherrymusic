app.factory('User', ['$resource',
    function($resource){
        return $resource(API_USER_URL + ':id/', null);
    }
]);