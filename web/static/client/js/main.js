
LOCAL_STORAGE = 0;

app = angular.module('CherryMusicClient', [
    'ui.bootstrap',
    'ui.bootstrap.tpls',
    'dndLists',
    'ngResource',
    'ngDropdowns',
    'ngCookies',
    'ngSanitize',
    'ngRoute',
    'cfp.hotkeys',
    'ngFileUpload',
    'ngAnimate',
    'growlNotifications',
]);

angular.module('angularDjangoRegistrationAuthApp', [

])
app.config(function($resourceProvider) {
  $resourceProvider.defaults.stripTrailingSlashes = false;
});

app.config(['$httpProvider', function($httpProvider){
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
}]);