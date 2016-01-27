app.factory('UserSettings', ['$resource',
    function($resource){
        return $resource(API_USER_SETTINGS_URL + ':id/', null,
        {
            'update': { method:'PUT' }
        });
    }
]);