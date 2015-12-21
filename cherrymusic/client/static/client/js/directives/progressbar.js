/**
 * Created by tom on 6/20/15.
 */
app.directive('progressBar', [
    function() {
        return {
            restrict: 'E',
            templateUrl: function(elem, attrs){
                if(attrs['kindOfBar'] == 'jp'){
                    return STATIC_FILES + 'client/templates/progressbars/jp-bar.html';
                };
                if( attrs['kindOfBar'] == 'volume'){
                    return STATIC_FILES + 'client/templates/progressbars/volume-bar.html';
                };
            },
            scope: {
                percentage: '@',
                kindOfBar: '@'
            },
            replace: true,
            link: function(scope, element, attributes){
                scope.element = element[0];
                scope.jump = function(event){
                    var jumpTo = null;

                    if(attributes.kindOfBar == 'jp'){
                        jumpTo = 'JUMP_TO_UNIT'
                    }
                    else if(attributes.kindOfBar == 'volume'){
                        jumpTo = 'VOLUME_TO_UNIT'
                    };

                    scope.$emit(jumpTo, (event.clientX - scope.element.getBoundingClientRect().left) / scope.element.offsetWidth);
                }
            }
        }
    }
]);