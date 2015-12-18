/**
 * Created by tom on 9/6/15.
 */
app.factory('track', [function(){
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