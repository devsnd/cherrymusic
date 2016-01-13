app.factory('Directory', ['$resource',
    function($resource){
        return $resource(API_DIRECTORY_URL + ':id/');
    }
]);