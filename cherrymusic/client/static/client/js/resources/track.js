app.factory('Track', [function(){
    var TYPE_FILE = 0;
    return {
        fromFile: function(file){
            return {
                type: TYPE_FILE, // file
                data: file,
            }
        }
    }
}]);