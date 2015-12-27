
app.filter('timeformat', function() {
    return function(input) {
        input = parseInt(input) || 0;
        var hours = Math.floor(input / 3600);
        var minutes = Math.floor((input % 3600) / 60);
        if(minutes < 10){
            minutes = '0' + minutes;
        }
        var seconds = Math.floor(input % 60);
        if(seconds < 10){
            seconds = '0' + seconds;
        }
        if(hours > 0){
            return hours+':'+minutes+':'+seconds;
        } else {
            return minutes+':'+seconds;
        }
    };
});
