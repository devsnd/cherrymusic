/**
 * Created by tom on 6/20/15.
 */


app.directive('fileBrowser', [
    function() {
        return {
            restrict: 'E',
            templateUrl: STATIC_FILES + 'client/templates/filebrowser.html',
            scope: {
                content: '='
            },
            controller: function ($scope) {
                $scope.breadcrumbs = [];
                // recreate the breadcrumbs when the content changes
                $scope.$watch('content', function(content){
                    $scope.breadcrumbs = $scope.getBreadcrumbs(content.current_path);
                });

                $scope.baseDirNotIndexed = function(content){
                    return (
                        content.current &&
                        content.current.parent === null
                        && !content.files.length
                        && !content.directories.length
                    );
                };

                $scope.indexingStarted = false;
                $scope.indexLibrary = function(path){
                    $scope.$emit('INDEX_DIRECTORY', path)
                    $scope.indexingStarted = true;
                };

                $scope.loadPreviousDirectory = function(directory){
                    console.log(directory);
                    var splitPaths = directory.split('/');
                    var previousPath = splitPaths.slice(0, splitPaths.length - 1).join('/');
                    if(previousPath == ''){
                        previousPath = '.';
                    };
                    $scope.loadDirectory(previousPath);
                }

                $scope.loadDirectory = function(directory){
                    $scope.$emit('LOAD_DIRECTORY', directory);
                };

                $scope.addToPlaylist = function(file){
                    $scope.$emit('ADD_FILE_TO_PLAYLIST', file);
                };

                $scope.addAllFilesToPlaylist = function(files){
                    files.forEach(function(file){
                        $scope.addToPlaylist(file);
                    });
                };

                $scope.albumArtUrl = function(filepath){
                    return API_ALBUMART_URL + filepath
                };

                $scope.getBreadcrumbs = function(currentPath){
                    if(currentPath === undefined){
                        return [];
                    }
                    var pathParts = currentPath.split('/');
                    var breadCrumbs = [{name: 'Root', path: ''}];
                    for(var i=0; i<pathParts.length; i++){
                        var dirPath = pathParts.slice(0, i + 1).join('/');
                        breadCrumbs.push(
                            {
                                name: pathParts[i],
                                path: dirPath
                            }
                        )
                    }
                    return breadCrumbs;
                };
            }
        }
    }
]);

app.directive('errSrc', function() {
  return {
    link: function(scope, element, attrs) {
      var defaultSrc = attrs.src;
      element.bind('error', function() {
        if(attrs.errSrc) {
            element.attr('src', attrs.errSrc);
        }
        else if(attrs.src) {
            element.attr('src', defaultSrc);
        }
      });
    }
  }
});
