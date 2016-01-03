app.factory('Directory', ['$resource',
    function($resource){
        return $resource(API_URL + 'directory/:id/');
    }
]);