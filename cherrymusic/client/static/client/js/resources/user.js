app.factory('User', ['$http', '$rootScope', function($http, $rootScope){
    return $http.get(API_URL + 'user/1').then(
        function (response){
            $rootScope.user = response.data;
        },
        function (response)
        {
            $rootScope.user = response.data;
        });
}]);

app.factory('UserList', ['$http', '$rootScope', function($http, $rootScope){
    return $http.get(API_URL + 'user/').then(
        function (response){
            $rootScope.userList = response.data;
        },
        function (response)
        {
            $rootScope.userList = response.data;
        });
}]);