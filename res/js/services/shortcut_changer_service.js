app.factory('ShortcutChangerService', function($q){
    return {
        getKey: function(){
            var deferred = $q.defer();
            $('#shortcut-changer span').html('Hit any key to set shortcut for<br><b><i>'+optionname+'</i></b><br><br>Press <b>escape</b> or <b>space</b> to cancel.');
            $('#shortcut-changer').fadeIn('fast');
            $('#shortcut-changer input').val('');
            $('#shortcut-changer input').focus();
            var keydownhandler = function(e){
                if (e.altKey) return;
                if (e.shiftKey) return;
                if (e.ctrlKey) return;
                if (e.metaKey) return;
                var keyboardsetterend = function(){
                    $('#shortcut-changer input').unbind('keydown',keydownhandler);
                    $('html').unbind('keydown',keydownhandler);
                    $('#shortcut-changer').fadeOut('fast');
                }
                if(e.which && e.which !== 27 && e.which !== 32){ //do not bind unrecognised keys or escape / space
                    deferred.resolve(e.which)
                    optionSetter(option,e.which,keyboardsetterend,keyboardsetterend);
                }
                keyboardsetterend();
                return false;
            }
            $('#shortcut-changer input').bind('keydown',keydownhandler);
            $('html').bind('keydown',keydownhandler);
        }
    }
});