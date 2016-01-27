/**
 * Created by tom on 6/20/15.
 */
app.directive('file', [
    function() {
        return {
            restrict: 'E',
            templateUrl: function(elem, attrs){
                if(attrs['file'] == 'track.data' && (attrs['model'] == undefined)){
                    return STATIC_FILES + 'client/templates/file/file-playlist.html';
                }
                else if( attrs['file'] == 'currentPlayingTrack.data'){
                    return STATIC_FILES + 'client/templates/file/file-current-track.html';
                }
                else {
                    return STATIC_FILES + 'client/templates/file/default.html';
                }
            },
            scope: {
                file: '=',
                model: '=',
                onRemove: '&',
                onPlay: '&'
            },
            replace: true
        }
    }
]);