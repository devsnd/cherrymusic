app.factory('FocusService', function($window, $timeout){
    // based on http://stackoverflow.com/a/25597540/1191373
    return {
        focus: function(elemId){
            $timeout(function() {
                var element = $window.document.getElementById(elemId);
                if(element){
                    element.focus();
                }
            });
        }
    }
})