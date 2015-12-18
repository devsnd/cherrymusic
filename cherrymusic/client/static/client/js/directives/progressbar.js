/**
 * Created by tom on 6/20/15.
 */
app.directive('progressBar', [
    function() {
        return {
            restrict: 'E',
            template: '<div class="jp-seek-bar progress jp-bar-seek" ng-click="jump($event)">'+
              '<div class="jp-play-bar progress progress-bar jp-bar-played" style="width: {{ percentage }}%"></div>'+
            '</div>',
            scope: {
                percentage: '@'
            },
            link: function(scope, element, attributes){
                scope.element = element[0];
                scope.jump = function(event){
                    scope.$emit('JUMP_TO_UNIT', event.clientX / scope.element.offsetWidth);
                }
            }
        }
    }
]);