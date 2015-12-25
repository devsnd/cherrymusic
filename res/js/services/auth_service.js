app.factory('AuthService', function(LegacyAPIService, UtilService){
    var userName, isAdmin;
    return {
        legacyInit: function(username, isadmin){
            // the legacy endpoint api/getconfiguration also contains the info
            // for the current user and permissions. This should later be
            // handled by a specific auth endpoint.
            userName = username;
            isAdmin = isadmin;
        },
        getUserName: function(){
            return userName;
        },
        isAdmin: function(){
            return isAdmin;
        },
        logout: function(){
            LegacyAPIService.post('api/logout').then(function(){
                UtilService.reloadPage();
            });
        },
        setPassword: function(oldPassword, newPassword){
            return LegacyAPIService.post(
                'api/userchangepassword',
                {
                    "oldpassword": oldPassword,
                    "newpassword": newPassword
                }
            )
        }
    }
})