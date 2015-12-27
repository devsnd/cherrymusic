app.factory('UserSettings', ['$resource',
    function($resource){
        return $resource(API_URL + 'user-settings/:id/', null,
        {
            'update': { method:'PUT' }
        });
    }
]);