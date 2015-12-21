/**
 * Created by tom on 6/14/15.
 */
app = angular.module('CherryMusicClient', [
    'ui.bootstrap',
    'ui.bootstrap.tpls',
    'dndLists',
    'ngResource',
    'ngDropdowns',
    'ngCookies',
    'ngSanitize',
    'ngRoute',
]);

angular.module('angularDjangoRegistrationAuthApp', [

])
app.config(function($resourceProvider) {
  $resourceProvider.defaults.stripTrailingSlashes = false;
});

app.config(['$compileProvider', function ($compileProvider) {
  $compileProvider.debugInfoEnabled(false);
}]);
