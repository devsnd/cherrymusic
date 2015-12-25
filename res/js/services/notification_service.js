app.factory('NotificationService', function($timeout){
    var notifications = [];
    var notificationAutoDismissalTime = 5000; //msec
    var notificationId = 0;

    var createNotification = function(type, message){
        notificationId += 1;
        notifications.push({
            message: message,
            type: type,
            timeCreated: +new Date(),
            id: notificationId
        });
        $timeout(cleanUp, notificationAutoDismissalTime);
    }

    var cleanUp = function(){
        var dismissTime = +new Date() - notificationAutoDismissalTime;
        notifications = notifications.filter(function(notification){
            if(notification.timeCreated < dismissTime){
                return false
            }
            return true;
        })
    }

    return {
        dismiss: function(toDismiss){
            notifications = notifications.filter(function(notification){
                return notification.id != toDismiss.id;
            });
        },
        getNotifications: function(){
            return notifications;
        },
        error: function(message) {
            createNotification('error', message);
        },
        success: function(message){
            createNotification('success', message);
        },
        info: function(){
            createNotification('info', message);
        },
    }
});