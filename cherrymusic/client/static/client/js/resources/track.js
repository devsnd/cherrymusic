app.factory('Track', [function(){
    return {
        fromFile: function(file){
            return {
                type: TYPE_FILE, // file
                data: file,
            }
        }
    }
}]);