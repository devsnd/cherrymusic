app.directive('cmBusy', function() {
    /*
    A Busy Indicator:

    Usage:

    <someelem cm-busy="somevalue" />

    if the value evaluates to true, the busy indicator will overlay the someelem
    with an animation and block any further user input.
    */
    var busyIndicator;
    return {
        restrict: 'A',
        scope: {
          cmBusy: '='
        },
        link: function(scope, element, attrs) {
            // create the busy indicator dom element
            busyIndicator = angular.element('<div class="busy-indicator"></div>');
            element.prepend(busyIndicator);

            // register the watcher to activate the busy indicator
            scope.$watch('cmBusy', function(newValue, oldValue){
                isBusy = !!newValue;
                if(isBusy){
                    // recalculate the busy indicator position
                    width = 'width: '+element[0].offsetWidth+'px;';
                    height = 'height: '+element[0].offsetHeight+'px;';
                    busyIndicator.attr('style','position: absolute;'+width+height);
                    busyIndicator.css('display', 'block');
                } else {
                    // hide the busy indicator
                    busyIndicator.css('display', 'none');
                }
            });
        }
    };
});