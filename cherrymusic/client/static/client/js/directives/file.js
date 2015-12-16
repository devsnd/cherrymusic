/**
 * Created by tom on 6/20/15.
 */
app.directive('file', [
    function() {
        return {
            restrict: 'E',
            templateUrl: function(elem, attrs){
                //console.log(elem);
                console.log(attrs);
                if(attrs['file'] == 'track.data'){
                    return STATIC_FILES + 'client/templates/file-playlist.html';
                }
                else {
                    return STATIC_FILES + 'client/templates/file.html';
                }
            },
            scope: {
                file: '=',
                onRemove:"&",
                onPlay:"&"
            }
        }
    }
]);