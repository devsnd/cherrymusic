app.factory('AdminService', function(LegacyAPIService, ConfigService, UtilService, $q){
    function dec2Hex(dec){
        var hexChars = "0123456789ABCDEF";
        var a = dec % 16;
        var b = (dec - a)/16;
        hex = hexChars.charAt(b) + hexChars.charAt(a);
        return hex;
    }

    function userNameToHexColor(username){
        username = username.toUpperCase();
        username+='AAA';
        var g = ((ord(username[0])-65)*255)/30;
        var b = ((ord(username[1])-65)*255)/30;
        var r = ((ord(username[2])-65)*255)/30;
        return '#'+dec2Hex(r)+dec2Hex(g)+dec2Hex(b);
    }

    return {
        deleteUser: function(user){
            return LegacyAPIService.post('api/userdelete', {userid: user.id});
        },
        permitDownload: function(user, allowDownload){
            return LegacyAPIService.post(
                'api/setuseroptionfor', 
                {
                    'optionkey': 'media.may_download',
                    'optionval': allowDownload,
                    'userid': user.id,
                }
            );
        },
        createUser: function(username, password, isAdmin){
            return LegacyAPIService.post(
                'api/adduser',
                {
                    'username': username,
                    'password': password,
                    'isadmin': !!isAdmin
                }
            )
        },
        fetchUserList: function(){
            var deferred = $q.defer();
            LegacyAPIService.post('api/getuserlist').then(function(results){
                results = JSON.parse(results);
                var servertime = results.time;
                var userList = results.userlist.map(function(user){
                    var lastSeenRelSec = servertime - user.last_time_online
                    var isOnline = lastSeenRelSec < ConfigService.getHeartbeatIntervalSec();
                    return {
                        id: user.id,
                        username: user.username,
                        mayDownload: user.may_download,
                        isOnline: isOnline,
                        lastSeenRelSec: lastSeenRelSec,
                        lastSeenReadable: UtilService.time2text(lastSeenRelSec),
                        isDeletable: user.deletable,
                        isAdmin: !!user.admin,
                        color: userNameToHexColor(user.username)
                    }
                });
                deferred.resolve(userList);
            }, function(){
                deferred.reject();
            })
            return deferred.promise;
        },
        updateMusicLibrary: function(){
            return LegacyAPIService.post('api/updatedb');
        }
    }
});
