app.factory('UtilService', function(){
    // random stuff i don't know where to put
    return {
        reloadPage: function() {
            //reconstruct url to suppress page reload post-data warning
            var reloadurl = window.location.protocol+'//'+window.location.host;
            window.location.href = reloadurl;
        },
        time2text: function (sec){
            var abssec = Math.abs(sec);
            var minutes = parseInt(abssec/60);
            var hours = parseInt(minutes/60)
            var days = parseInt(hours/24);
            var weeks = parseInt(days/7);
            var months = parseInt(days/30);
            var years = parseInt(days/365);
            var t='';
            if(abssec < 30){
                return 'just now'
            } else {
                if(years != 0){
                    t = years == 1 ? 'a year' : years+' years';
                    if(years > 20){
                        t = 'a long time';
                    }
                } else if(months != 0){
                    t = months == 1 ? 'a month' : months+' months';
                } else if(weeks != 0){
                    t = weeks == 1 ? 'a week' : weeks+' weeks';
                } else if(days != 0){
                    t = days == 1 ? 'a day' : days+' days';
                } else if(hours != 0){
                    t = hours == 1 ? 'an hour' : hours+' hours';
                } else if(minutes != 0){
                    t = minutes > 25 ? 'half an hour' : minutes+' minutes';
                    if (minutes == 1){
                        t = 'a minute';
                    }
                } else {
                    t = 'a few seconds'
                }
                return sec > 0 ? t+' ago' : 'in '+t;
            }
        }
    }
});