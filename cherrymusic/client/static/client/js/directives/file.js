/**
 * Created by tom on 6/20/15.
 */
app.directive('file', [
    function() {
        return {
            restrict: 'E',
            template: '<span ng-if="file.meta_title">'+
                    '{{ file.meta_track }} '+
                    '{{ file.meta_artist }} - {{ file.meta_title }} '+
                    '({{ file.meta_duration | timeformat }})'+
                '</span>'+
                '<span ng-if="!file.meta_title">'+
                    '{{ file.filename }}'+
                '</span>',
            scope: {
                file: '='
            }
        }
    }
]);