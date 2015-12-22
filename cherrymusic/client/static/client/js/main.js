
TYPE_FILE = 0;

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
]);

angular.module('angularDjangoRegistrationAuthApp', [

])
app.config(function($resourceProvider) {
  $resourceProvider.defaults.stripTrailingSlashes = false;
});

app.config(['$compileProvider', function ($compileProvider) {
  $compileProvider.debugInfoEnabled(false);
}]);
