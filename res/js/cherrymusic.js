//
// CherryMusic - a standalone music server
// Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
//
// Project page:
//   http://fomori.org/cherrymusic/
// Sources on github:
//   http://github.com/devsnd/cherrymusic/
//
// licensed under GNU GPL version 3 (or later)
//
// CherryMusic is based on
//   jPlayer (GPL/MIT license) http://www.jplayer.org/
//   CherryPy (BSD license) http://www.cherrypy.org/
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>
//

var browser = detectBrowser();
//see http://www.w3schools.com/html/html5_audio.asp for available formats per browser
if(['msie','safari'].indexOf(browser) != -1){
    var encoderPreferenceOrder = ['mp3','ogg'];
} else {
    var encoderPreferenceOrder = ['opus', 'ogg','mp3'];
}

var SERVER_CONFIG = {};
var availableEncoders = undefined;
var availablejPlayerFormats = ['opus', 'mp3','ogg'];
var availableDecoders = undefined;
var transcodingEnabled = undefined;
var userOptions = undefined;
var isAdmin = undefined;
var loggedInUserName = undefined;
var REMEMBER_PLAYLIST_INTERVAL = 3000;
var CHECK_MUSIC_PLAYING_INTERVAL = 2000;
var HEARTBEAT_INTERVAL_MS = 30*1000;

var playlistSelector = '.jp-playlist';
var previousSorted = undefined

var executeAfterConfigLoaded = []


/**
 * This function can call the cherrymusic api (v1)
 * api(String actionname,   -> action name as defined in httphandler.py
 *     [data,]              -> simple js object containing the data
 *     successfunc,         -> fucntion to be called on success
 *     errorfunc,           -> function to be called on error
 *     completefunc)        -> function to be called after error/success
 */
function api(){
    "use strict";
    var action = arguments[0];
    var has_data = !(typeof arguments[1] === 'function');
    var data = {};
    if(has_data){
        data = arguments[1];
    }
    var successfunc = arguments[has_data?2:1];
    var errorfunc = arguments[has_data?3:2];
    var completefunc = arguments[has_data?4:3];

    if(!successfunc) successfunc = function(){};
    if(!completefunc) completefunc = function(){};

    var successFuncWrapper = function(successFunc){
        return function handler(json){
            var result = $.parseJSON(json);
            if(result.flash){
                successNotify(result.flash);
            }
            successFunc(result.data);
        }
    }

    //wrapper for all error handlers:
    var errorFuncWrapper = function(errorFunc){
        return function(httpstatus){
            if(httpstatus.status == 401){
                /* if a request get's a 401, that means the user was logged
                 * out, so we reload to show the login page. */
                reloadPage();
            }
            errorFunc();
        }
    }
    if(!errorfunc){
        //default error handler
        errorfunc = function(){
            errorFunc('Error calling API function "'+action+'"')();
        };
    }
    $.ajax({
        url: 'api/'+action,
        context: $(this),
        type: 'POST',
        data: {'data': JSON.stringify(data)},
        success: successFuncWrapper(successfunc),
        error: errorFuncWrapper(errorfunc),
        complete: completefunc,
    });
}

htmlencode = function(val){
    return $('<div />').text(val?val:'').html();
}
htmldecode = function(val){
    return $('<div />').html(val?val:'').text();
}

function errorFunc(msg){
    "use strict";
    return function(){
        window.console.error('CMError: '+msg);
        displayNotification(msg,'error');
    };
}
function successNotify(msg){
    return function(){
        displayNotification(msg,'success');
    };
}

function hideNotification(selector){
    var notification = $(selector);
    if(notification.length){
        notification.fadeOut('slow', function(){
            notification.remove();
        });
    }
}

function displayNotification(msg, type, duration){
    if(typeof duration === 'undefined'){
        duration = 5000;
    }
    var selector = '#errormessage:contains(' + msg + ')';
    var notificationExists = Boolean($(selector).length);
    if(notificationExists) {
        return;
    }
    var unique_class_id = 'notification-'+Math.floor(Math.random()*1000000);
    var cssclass;
    if(type == 'error'){
        cssclass = 'alert-danger';
    } else if(type == 'success'){
        cssclass = 'alert-success';
    } else {
        cssclass = 'alert-info';
    }
    cssclass += ' '+unique_class_id;
    templateLoader.render_append(
        'flash-message',
        {
            msg : msg,
            cssclass: cssclass,
        },
        $('#errormessage')
    );
    window.setTimeout('hideNotification(".'+unique_class_id+'")', duration)
}

/*******************
CONFIGURATION LOADER
*******************/
function loadConfig(executeAfter){
    "use strict";
    var success = function(data){
        var dictatedClientConfig = data;
        /** DEPRECATED GLOBAL VARIABLES **/
        availableEncoders = dictatedClientConfig.getencoders;
        availableDecoders = dictatedClientConfig.getdecoders;
        transcodingEnabled = dictatedClientConfig.transcodingenabled;
        isAdmin = dictatedClientConfig.isadmin;
        loggedInUserName = dictatedClientConfig.username;

        /** USE SERVER CONFIG INSTEAD **/
        SERVER_CONFIG = {
            'available_encoders': dictatedClientConfig.getencoders,
            'available_decoders': dictatedClientConfig.getdecoders,
            'transcoding_enabled': dictatedClientConfig.transcodingenabled,
            'is_admin': dictatedClientConfig.isadmin,
            'user_name': dictatedClientConfig.username,
            'serve_path': dictatedClientConfig.servepath,
            'transcode_path': dictatedClientConfig.transcodepath,
            'auto_login': dictatedClientConfig.auto_login,
            'version': dictatedClientConfig.version,
        }

        executeAfter();
        if(isAdmin){
            $('a[href="#adminpanel"]').show();
        }
        if(SERVER_CONFIG.auto_login){
            $('#logout-menu-button').parent('li').addClass('disabled');
            $('#logout-menu-button').attr('onclick', '');
            $('#logout-menu-button').attr('title', 'Cannot logout: Auto-Login enabled');
        }
        $('#aboutModal #cherrymusic-version').html(SERVER_CONFIG.version)
    };
    var error = errorFunc("Could not fetch client configuration, CherryMusic will not work. Clearing the browser cache might help.");
    api('getconfiguration', {}, success, error);
}

/************
 * USER OPTIONS
 * **********/

function loadUserOptions(onSuccess){
    var success = function(userOptionsLoaded){
        userOptions = userOptionsLoaded;
        if(typeof onSuccess !== 'undefined'){
            onSuccess();
        }
        $('#custom_theme-primary_color').val(userOptions.custom_theme.primary_color);
        $('#custom_theme-white_on_black').attr('checked',userOptions.custom_theme.white_on_black);

        $('#keyboard_shortcuts-next').html(String.fromCharCode(userOptions.keyboard_shortcuts.next));
        $('#keyboard_shortcuts-prev').html(String.fromCharCode(userOptions.keyboard_shortcuts.prev));
        $('#keyboard_shortcuts-stop').html(String.fromCharCode(userOptions.keyboard_shortcuts.stop));
        $('#keyboard_shortcuts-play').html(String.fromCharCode(userOptions.keyboard_shortcuts.play));
        $('#keyboard_shortcuts-pause').html(String.fromCharCode(userOptions.keyboard_shortcuts.pause));
        $('#keyboard_shortcuts-search').html(String.fromCharCode(userOptions.keyboard_shortcuts.search));

        $('#misc-autoplay_on_add').attr('checked',userOptions.misc.autoplay_on_add);
        $('#ui-confirm_quit_dialog').attr('checked',userOptions.ui.confirm_quit_dialog);
        $('#ui-display_album_art').attr('checked',userOptions.ui.display_album_art);

        handle_useroption_force_transcode_bitrate();
    };
    api('getuseroptions', success);
}

var waitForServerOptions = function(callback) {
    var serverOptionsAreLoaded = Boolean(Object.keys(SERVER_CONFIG).length);
    if(!serverOptionsAreLoaded) {
        var timeout = 500;
        setTimeout(callback, timeout);
        return true;
    }
    return false;
};

var handle_useroption_force_transcode_bitrate = function() {
    if(waitForServerOptions(handle_useroption_force_transcode_bitrate)) {
        console.info('useroption handler waiting for server options...');
        return;
    }
    var forced_bitrate = userOptions.media.force_transcode_to_bitrate;
    if (SERVER_CONFIG['transcoding_enabled']) {
        var select = "select[name='media-force_transcode_to_bitrate']";
        var selected = select + "> option[value='x']".replace(/x/, forced_bitrate);
        var deselected = selected.replace(/value=/, 'value!=');
        $(selected).attr('selected', 'selected');
        $(deselected).removeAttr('selected');
        $("#media-force_transcode_to_bitrate-display").val(forced_bitrate);
        if([0, 48, 64, 96, 128, 320].indexOf(forced_bitrate) < 0) {
            console.log("Unknown bitrate value:", forced_bitrate);
        }
    } else {
        var optionContainer = $("#media-force_transcode_to_bitrate-container");
        optionContainer.find(".success").hide();
        if(forced_bitrate) {
            userOptions.media.force_transcode_to_bitrate = false;
            var msg = 'WARNING Cannot enforce bitrate limit of :value kbps: server does not transcode!';
            var extra = ' <a href="#userOptions" role="button" class="btn btn-info" data-toggle="modal">Disable limit in options menu</a>';
            msg = msg.replace(/:value/, forced_bitrate);
            displayNotification(msg + extra, 'error');
            var errorArea = optionContainer.find(".error");
            errorArea.find(".msg").html(msg);
            errorArea.show();
        }
    }
};

var optionSetter = function(name, val, success, error){
    busy('#userOptions .content').hide().fadeIn();
    api('setuseroption',
        {
            'optionkey':name,
            'optionval':val
        },
        function(){ success(); loadUserOptions(); },
        error,
        function(){ busy('#userOptions .content').fadeOut('fast'); }
    )
}
keyboard_shortcut_setter = function(option, optionname){
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
            optionSetter(option,e.which,keyboardsetterend,keyboardsetterend);
        }
        keyboardsetterend();
        return false;
    }
    $('#shortcut-changer input').bind('keydown',keydownhandler);
    $('html').bind('keydown',keydownhandler);
}

function busy(selector, rect){
    "use strict";
    var domelem = $(selector).children('.busy-indicator');
    if(domelem.length == 0){
        domelem = $('<div></div>');
        domelem.addClass('busy-indicator');
        $(selector).append(domelem);
    }
    var top, left, width, height;

    var pos = $(selector).position();
    top = 'top: '+pos.top+'px;';
    left = 'left: '+pos.left+'px;';
    width = 'width: '+$(selector).width()+'px;';
    height = 'height: '+$(selector).height()+'px;';

    domelem.attr('style','position: absolute;'+top+left+width+height);
    return domelem;
}

function search($form){
    "use strict";
    var $input = $form.find('input');
    if($input.val().trim() == ""){
        //make sure no spaces, so placeholder is shown
        $input.val('');
        $input.prop('placeholder', 'Search for what?');
        $input.focus();
        return false;
    }
    var searchstring = $input.val();
    var success = function(json){
        $('.searchinput').removeClass('searchinput-busy');
        new MediaBrowser('.search-results', json, 'Search: '+htmlencode(searchstring));
    };
    var error = function(){
        $('.searchinput').removeClass('searchinput-busy');
        errorFunc('failed loading search results')();
    };
    $('.searchinput').addClass('searchinput-busy');
    api('search', {'searchstring': searchstring}, success, error);
    return false;
}
function submitsearch(){
    search();
    return false;
}

/***
INTERACTION
***/


/* PLAYLIST CREATION AND MANAGEMENT END*/

ext2jPlayerFormat = function(ext){
    switch(ext){
        case "mp3": return "mp3";

        case "ogg":
        case "opus":
        case "oga": return "oga";

        case "m4a":
        case "mp4":
        case "aac": return "m4a";

        case "flac" : return "flac"

        case "wav": return "wav";

        case "weba": return "webma";
    }
}


/******************
PLAYLIST MANAGEMENT
******************/
function savePlaylistAndHideDialog(){
    "use strict";
    var name = $('#playlisttitle').val();
    var pub = $('#playlistpublic').prop('checked')?true:false;
    if(name.trim() !== ''){
        var pl = playlistManager.newPlaylistFromEditing();
        savePlaylist(pl.id,name,pub);
        $('#saveplaylistmodal').modal('hide');
    }
    $(this).blur();
    return false;
}

function savePlaylist(plid,playlistname,ispublic,overwrite){
    "use strict";
    var pl = playlistManager.getPlaylistById(plid);
    overwrite = Boolean(overwrite);
    ispublic = ispublic || pl.public;
    playlistname = playlistname || pl.name;
    var success = function(){
        playlistManager.getPlaylistById(plid).name = playlistname;
        playlistManager.getPlaylistById(plid).public = ispublic;
        playlistManager.getPlaylistById(plid).saved = true;
        playlistManager.refresh();
        playlistManager.showPlaylist(plid);
    }
    busy('#playlist-panel').hide().fadeIn('fast');
    api('saveplaylist',
        {
            'playlist':pl.jplayerplaylist.playlist,
            'public':ispublic,
            'playlistname':playlistname,
            'overwrite':overwrite,
        },
        success,
        errorFunc('error saving playlist'),
        function(){busy('#playlist-panel').fadeOut('fast')});
}
function getAddrPort(){
    m = (window.location+"").match(/(https?):\/\/([^/:]+)(?::(\d+))?/);   // won't work for URLs with "user:passw@host"
    // 0: whole match, 1: protocol, 2: host, 3: port or undefined
    // whole match = "$protocol://$host(:$port)?"
    return m[0];
}

function ord(c)
{
  return c.charCodeAt(0);
}

function showPlaylists(sortby, filterby){
    "use strict";
    var success = function(data){
        var addressAndPort = getAddrPort();
        var value_before = $('.playlist-filter-input').val();
        new MediaBrowser('.search-results', data, 'Playlist browser', false, {showPlaylistPanel: true});
        $('.playlist-filter-input').val(value_before);
    };
    var error = errorFunc('error loading external playlists');

    if(sortby == previousSorted){
        sortby = '-' + sortby; 
    }
    previousSorted = sortby;

    busy('.search-results').hide().fadeIn('fast');
    api('showplaylists',
        {'sortby': sortby,
         'filterby': filterby},
        success,
        error,
        function(){busy('.search-results').fadeOut('fast')}
    );
}

function changePlaylist(plid,attrname,value){
    window.console.log(plid);
    window.console.log(attrname);
    window.console.log(value);
    busy('#playlist-panel').hide().fadeIn('fast');
    api('changeplaylist',
        {
            'plid' : plid,
            'attribute' : attrname,
            'value' : value
        },
        function(){
            showPlaylists();
        },
        errorFunc('error changing playlist attribute'),
        function(){busy('#playlist-panel').fadeOut('fast')}
    );
}

function confirmDeletePlaylist(id,title){
    $('#deletePlaylistConfirmButton').off();
    $('#deletePlaylistConfirmButton').on('click', function(){
        busy('#playlist-panel').hide().fadeIn('fast');
        api('deleteplaylist',
            {'playlistid':  id},
            false,
            errorFunc('error deleting playlist'),
            function(){busy('#playlist-panel').fadeOut('fast')}
        );
        $('#dialog').fadeOut('fast');
        showPlaylists();
    });
    $('#deleteplaylistmodalLabel').html(Mustache.render('Really delete Playlist "{{title}}"',{title:title}));
    $('#deleteplaylistmodal').modal('show');
}

function loadPlaylist(playlistid, playlistlabel){
    var success = function(data){
        var tracklist = data;
        //transform tracks to jplayer format:
        //TODO rewrite jplayer playlist to support CM-music entry format
        var pl = playlistManager.newPlaylist([], playlistlabel);
        var animate = false;
        for(var i=0; i<tracklist.length; i++){
            playlistManager.addSong(tracklist[i].urlpath, tracklist[i].label, pl.id, animate);
        }
        pl.setSaved(true);
        pl.scrollToTrack(0);
    }
    api('loadplaylist',
        {'playlistid': playlistid},
        success,
        errorFunc('error loading external playlist'),
        function(){busy('#playlist-panel').fadeOut('fast')}
    )
}

function loadPlaylistContent(playlistid, playlistlabel){
    "use strict";
    var pldomid = "#playlist"+playlistid+' .playlist-content';
    if('' === $(pldomid).html().trim()){
        var success = function(data){
            new MediaBrowser(pldomid, data, playlistlabel, false);
            $("#playlist"+playlistid+' .playlist-detail-switch .glyphicon')
            .toggleClass('glyphicon-chevron-right')
            .toggleClass('glyphicon-chevron-down');
        };
        busy('#playlist-panel').hide().fadeIn('fast');
        api('loadplaylist',
            {'playlistid': playlistid},
            success,
            errorFunc('error loading external playlist'),
            function(){busy('#playlist-panel').fadeOut('fast')}
        );
    } else {
        $(pldomid).slideToggle('slow');
        $("#playlist"+playlistid+' .playlist-detail-switch .glyphicon')
            .toggleClass('glyphicon-chevron-right')
            .toggleClass('glyphicon-chevron-down');
    }
}

function randomPlaylist() {
    "use strict";
    playlistManager.clearQueue();
    var success = function(tracks){
        for (var i = 0; i < tracks.length; i++) {
            var track = tracks[i];
            playlistManager.addSong(track.urlpath, track.label)
        }
    };
    busy('#jplayer').hide().fadeIn('fast');
    api('generaterandomplaylist',
        success,
        errorFunc('error loading random playlist'),
        function(){busy('#jplayer').fadeOut('fast')}
    );
}

var lastPlaylistHeight = 0;
function resizePlaylistSlowly(){
    var currentHeight = $('.jp-playlist').height();
    if(lastPlaylistHeight <= currentHeight){
        $('#playlistContainerParent').animate({'min-height': currentHeight});
    }
    lastPlaylistHeight = currentHeight;
}

function download_editing_playlist(){
    var pl = playlistManager.getEditingPlaylist();
    var p = pl.jplayerplaylist.playlist;
    var track_urls = [];
    for(i=0; i<p.length; i++){
        track_urls.push(decodeURIComponent(p[i].url));
    }
    api('downloadcheck',
        {'filelist': track_urls},
        function(msg){
            if(msg == 'ok'){
                //add tracks to hidden form and call to call download using post data
                $('#download-redirect-files').val(encodeURIComponent(JSON.stringify(track_urls)));
                // disable confirm-to-quit for the download link (will be reenabled automatically)
                window.onbeforeunload = null
                $('#download-redirect').submit();
            } else {
                alert(msg);
            }
        },
        errorFunc('Failed to check if playlist may be downloaded')
    );
}

/*****
OTHER
*****/

function reloadPage(){
    //reconstruct url to suppress page reload post-data warning
    var reloadurl = window.location.protocol+'//'+window.location.host;
    window.location.href = reloadurl;
}

function logout(){
    "use strict";
    api('logout', reloadPage);
}

/** TEMPLATES **/
function TemplateLoader(template_path){
    this.template_path = template_path;
    this.loaded_templates = {};
    var self = this;
    this.get = function(template_name, callback){
        if(this.loaded_templates.hasOwnProperty(template_name)){
            callback(this.loaded_templates[template_name]);
        } else {
            $.get(
                this.template_path+'/'+template_name+'.html',
                function(data){
                    self.loaded_templates[template_name] = data;
                    if(typeof callback === 'undefined'){
                        window.console.log('preloaded template '+template_name);
                    } else {
                        callback(self.loaded_templates[template_name]);
                    }
                }
            );
        }
    }
    this.render = function(template_name, content, $jqobj){
        this.get(template_name, function(template){
            $jqobj.html(Mustache.render(template, content));
        });
    }
    this.render_append = function(template_name, content, $jqobj){
        this.get(template_name, function(template){
            $jqobj.append(Mustache.render(template, content));
        });
    };
    this.cached = function(template_name){
        if(this.loaded_templates.hasOwnProperty(template_name)){
            return this.loaded_templates[template_name];
        } else {
            window.console.error('Can not return unloaded template '+template_name+'!');
            return '';
        }
    }
}
var templateLoader = new TemplateLoader('res/templates');
//preload templates for mediabrowser
templateLoader.get('mediabrowser-directory');
templateLoader.get('mediabrowser-file');
templateLoader.get('mediabrowser-compact');
templateLoader.get('mediabrowser-message');
templateLoader.get('mediabrowser-playlist');
//preload templates for flash message
templateLoader.get('flash-message');
/***
ADMIN PANEL
***/

function updateUserList(){
    "use strict";
    var success = function(data){
        var htmllist = "";
        var response = $.parseJSON(data);
        var time = response['time'];
        var template_user_data = {'users': []};
        $.each(response['userlist'],function(i,e){
            var reltime = time - e.last_time_online;
            template_user_data['users'].push({
                isadmin: e.admin,
                may_download: e.may_download,
                isnotadmin: !e.admin,
                isdeletable: e.deletable,
                userid: e.id,
                isonline: reltime < HEARTBEAT_INTERVAL_MS/500,
                username: e.username,
                username_color: userNameToColor(e.username),
                fuzzytime: time2text(reltime),
            });
        });
        templateLoader.get('user-list', function(template){
            $('#adminuserlist').html(Mustache.render(template, template_user_data));
        });
    };
    busy('#adminuserlist').hide().fadeIn('fast');
    api('getuserlist',
        success,
        errorFunc('cannot fetch user list'),
        function(){busy('#adminuserlist').fadeOut('fast')}
    );
}
function addNewUser(){
    "use strict";
    var newusername = $('#newusername').val();
    var newpassword = $('#newpassword').val();
    var newisadmin = $('#newisadmin').prop('checked')?1:0;
    if(newusername.trim() === '' || newpassword.trim() === ''){
        return;
    }
    var success = function(data){
        $('#newusername').val('');
        $('#newpassword').val('');
        $('#newisadmin').prop('checked', false);
        updateUserList();
    };
    busy('#adminpanel').hide().fadeIn('fast');
    api('adduser',
        {
            'username':newusername,
            'password':newpassword,
            'isadmin':newisadmin
        },
        success,
        errorFunc('failed to add new user'),
        function(){busy('#adminpanel').fadeOut('fast')}
    );
}

function userDelete(userid){
    var success = function(data){
        updateUserList();
    };
    busy('#adminuserlist').hide().fadeIn('fast');
    api('userdelete',
        { 'userid':userid },
        success,
        errorFunc('failed to delete user'),
        function(){ busy('#adminuserlist').fadeOut('fast') }
    );
}

function userSetPermitDownload(userid, allow_download){
    var success = function(data){
        updateUserList();
    };
    busy('#adminuserlist').hide().fadeIn('fast');
    api('setuseroptionfor',
        {
            'optionkey': 'media.may_download',
            'optionval': allow_download,
            'userid': userid,
        },
        success,
        errorFunc('Failed to set user download state'),
        function(){busy('#adminuserlist').fadeOut('fast')}
    );
}

function userChangePassword(){
    if (! validateNewPassword($('#newpassword-change'), $('#repeatpassword-change'))) {
        return false;
    }
    var success = function(data){
        $('#changePassword').find('input').each(function(idx, el) { $(el).val(''); } );
        $('#changePassword').modal('hide');
        $('#userOptions').modal('hide');
        successNotify('Password changed successfully!')();
    };
    var error = function(){
        $('#oldpassword-change').val('');
        $('#oldpassword-change').focus();
        $("#changePassword").modal('attention');
    };
    busy('#changePassword').hide().fadeIn('fast');
    api('userchangepassword',
        {
            'oldpassword':$('#oldpassword-change').val(),
            'newpassword':$('#newpassword-change').val()
        },
        success,
        error,
        function(){busy('#changePassword').fadeOut('fast');}
    );
}
function validateNewPassword($newpwfield, $repeatpwfield){
    var newpw = $newpwfield.val();
    var repeatpw = $repeatpwfield.val();
    if (newpw == repeatpw) {
        $repeatpwfield.closest('.control-group').removeClass('error');
        return true;
    }
    $repeatpwfield.closest('.control-group').addClass('error');
    return false;
}

function userExportPlaylists() {
    var loc = window.location;
    var hostaddr = loc.protocol + '//' + loc.host;
    $('#exportPlaylists input[name=hostaddr]').val(hostaddr);
    $('#exportPlaylists form').submit();
    $('#exportPlaylists').modal('hide');
    $('#userOptions').modal('hide');
}

function enableJplayerDebugging(){
    $('#jplayer_inspector').jPlayerInspector({jPlayer:$('#jquery_jplayer_1'),visible:true});
    $('#jquery_jplayer_1').data().jPlayer.options.errorAlerts = true;
    $('#jquery_jplayer_1').data().jPlayer.options.warningAlerts = true;
    $('#jplayer_inspector_update_0').click();
}

function loadBrowser(directory, title){
    if(typeof directory === 'undefined'){
        directory = '';
    }
    if(typeof title === 'undefined'){
        title = 'Root';
    }
    var success = function(data){
        new MediaBrowser('.search-results', data, title);
    };
    busy('#searchfield').hide().fadeIn('fast');
    api('listdir',
        {'directory' : directory},
        success,
        errorFunc('failed to load file browser'),
        function(){busy('#searchfield').fadeOut('fast')});
}

/***
HELPER
***/

function endsWith(str, suffix) {
    "use strict";
    return str.indexOf(suffix, str.length - suffix.length) !== -1;
}
function getFileTypeByExt(filepath){
    "use strict";
    var extmatch = filepath.match(/.*?\.(\w+)$/);
    if(extmatch){
        return extmatch[1].toLowerCase();
    }
}

function detectBrowser(){
    var browsers = ['midori','firefox','msie','chrome','safari','opera']
    for(var i=0; i<browsers.length; i++){
        if(navigator.userAgent.toLowerCase().indexOf(browsers[i])!=-1){
            return browsers[i];
        }
    }
    return 'unknown';
}

/*****
 * UTIL
 * ***/
function unixtime(){
    var d = new Date;
    return parseInt(d.getTime() / 1000);
}

function time2text(sec){
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

function dec2Hex(dec){
    var hexChars = "0123456789ABCDEF";
    var a = dec % 16;
    var b = (dec - a)/16;
    hex = hexChars.charAt(b) + hexChars.charAt(a);
    return hex;
}

function userNameToColor(username){
    username = username.toUpperCase();
    username+='AAA';
    var g = ((ord(username[0])-65)*255)/30;
    var b = ((ord(username[1])-65)*255)/30;
    var r = ((ord(username[2])-65)*255)/30;
    return '#'+dec2Hex(r)+dec2Hex(g)+dec2Hex(b);
}

/*****************
 * KEYBOARD SHORTCUTS
 * ***************/
function initKeyboardshortcuts(){
    $(window.document).bind('keydown', keyboardShortcuts);
    //disable space bar scrolling
    $(document).keydown(function (e) {
        var focusedElement = $("*:focus");
        var inputFieldFocused = focusedElement.length > 0;
        var key = e.charCode ? e.charCode : e.keyCode ? e.keyCode : 0;
        if (key === 32 && !inputFieldFocused) e.preventDefault();
    });
}
function keyboardShortcuts(e){
    //we don't want to ruin all the nice standard shortcuts.
    if (e.altKey) return;
    if (e.shiftKey) return;
    if (e.ctrlKey) return;
    if (e.metaKey) return;

    var actions = { 'next' :    function(e){playlistManager.cmd_next()},
                    'pause' :   function(e){playlistManager.cmd_pause()},
                    'play' :    function(e){playlistManager.cmd_play()},
                    'prev' :    function(e){playlistManager.cmd_previous()},
                    'search' :  function(e){$('#searchform input').focus().select(); e.preventDefault();},
                    'stop' :    function(e){playlistManager.cmd_stop()},
                    };
    var mediaKeys = { 'MediaNextTrack' :        'next',
                      'MediaPlayPause' :        'pause', //The pause action is really play/pause, while the play action is only play.
                      'MediaPreviousTrack' :    'prev',
                      'MediaStop' :             'stop'
                      //Volume up/down/mute keys also exist, but ignore them because they already control system volume.
                      };
    var triggerAction = function (action){
        window.console.log('triggering: '+action);
        actions[action](e);
    };

    if (e.key && mediaKeys[e.key]){
        triggerAction(mediaKeys[e.key]);
    } else {
        var focusedElement = $("*:focus");
        var inputFieldFocused = focusedElement.length > 0;
        if(inputFieldFocused){
            if(e.which === 27){ //escape -> unfocus
                focusedElement.blur();
            }
        } else if(e.which === 32){
            triggerAction('pause');
        } else {
            for(var action in actions){
                if(e.which === userOptions.keyboard_shortcuts[action] && userOptions.keyboard_shortcuts[action]){
                    triggerAction(action);
                    break;
                }
            }
        }
    }
}

function sendHeartBeat(){
    api('heartbeat',
        function(){ /*removeError('connection to server lost') */ },
        errorFunc('connection to server lost'),
        true)
    window.setTimeout('sendHeartBeat()', HEARTBEAT_INTERVAL_MS);
}

function userOptionCheckboxListener(htmlid, optionname){
    REQUIRES_RELOAD_ON_ENABLE = ['#ui-confirm_quit_dialog'];
    $(htmlid).on('change',function(){
        var self = this;
        optionSetter(   optionname,
                        $(this).is(':checked'),
                        function(){
                            if($(self).is(':checked')){
                                if(REQUIRES_RELOAD_ON_ENABLE.indexOf(htmlid) != -1){
                                    alert('You need to reload the page for this setting to take effect.')
                                }
                            }
                        },
                        errorFunc('Error setting option! '+optionname)
        );
    });
}

function userOptionMultivalListener(selector, optionname) {
    $(selector).on('change',function(){
        var self = this;
        optionSetter(   optionname,
                        $(this).val(),
                        function(){
                        },
                        errorFunc('Error setting option! '+optionname)
        );
    });
}

/*****************************
CONDITIONAL USER INTERFACE
 *****************************/

function show_ui_conditionally(selectors, conditions_table){
    var conditions_met = [];
    for(var condition_name in conditions_table){
        if(conditions_table.hasOwnProperty(condition_name)){
            if(conditions_table[condition_name]){
                conditions_met.push(condition_name);
            }
        }
    }
    //support for single string as first argument
    if(!selectors instanceof Array){
        selectors = [selectors];
    }
    for(var i=0; i<selectors.length; i++){
        //check all buttons for their show conditions and hide/show them
        $(selectors[i]+' > [show-cond]').each(function(i, e){
            var ui_element = $(e);
            var conditions_needed = ui_element.attr('show-cond').split(' ');
            ui_element.show();
            $.each(conditions_needed, function(i, e){
                if(conditions_met.indexOf(e) < 0){
                    ui_element.hide();
                    return false;
                }
            });
        });
    }
}

function jPlayerIsPlaying(){
    return !$('#jquery_jplayer_1').data().jPlayer.status.paused;
}

function dontCloseWindowIfMusicPlays(){
    if(userOptions.ui.confirm_quit_dialog){
        if(jPlayerIsPlaying()){
            if(window.onbeforeunload === null){
                // register close dialog if music is playing
                window.onbeforeunload = function() {
                  return "This will stop the playback. Do you really want to close CherryMusic?";
                }
            }
        } else {
            if(window.onbeforeunload !== null){
                // remove close dialog if no music is playing
                window.onbeforeunload = null;
            }
        }
        window.setTimeout("dontCloseWindowIfMusicPlays()", CHECK_MUSIC_PLAYING_INTERVAL)
    } else {
        window.onbeforeunload = null;
    }
}

function searchAlbumArt(){
    busy('#changeAlbumArt .modal-body').hide().fadeIn('fast');
    var success = function(urllist){
        $('.coverart-tryout').html('');
        for(var i=0; i<urllist.length; i++){
            var html =  '<div class="album-art-choice">'+
                            '<img width="80" height="80" src="'+urllist[i]+'"'+
                            ' onclick="pickCoverArt($(this))" '+
                            '" />'+
                        '</div>';
            $('.coverart-tryout').append(html);
        }
    }
    api('fetchalbumarturls',
        {'searchterm': $('#albumart-search-term').val()},
        success,
        errorFunc('Error fetching image urls'),
        function(){busy('#changeAlbumArt .modal-body').fadeOut('fast')});
}

function pickCoverArt(img){
    var imagesrc = $(img).attr('src');
    var dirname = decodeURIComponent($('#changeAlbumArt').attr('data-dirname'));
    var success = function(){
        $('#changeAlbumArt').modal('hide');
        //reload cover art:
        var folder_div = $('.list-dir[dir="'+dirname+'"]')
        //force reload image
        var folder_image = folder_div.find('img');
        folder_image.attr('src', folder_image.attr('src')+'&reload=1');
    }
    api('albumart_set',
        {
            'directory': dirname,
            'imageurl': imagesrc,
        },
        success
    );
}

function displayMessageOfTheDay(){
    api('getmotd',
        function(resp){
            if(resp.type == 'update'){
                html = Mustache.render(
                    '<a href="http://fomori.org/cherrymusic/">'+
                        'CherryMusic {{version}} is available!'+
                        '<h2>download now →</h2>'+
                    '</a><hr>'+
                    '<h3>{{features_count}} new {{feature_title}}:</h3>'+
                    '<ul class="feature-list">'+
                    '   {{#features}}<li>{{.}}</li>{{/features}}'+
                    '</ul>'+
                    '<h3>{{fixes_count}} {{fixes_title}}:</h3>'+
                    '<ul class="feature-list">'+
                    '   {{#fixes}}<li>{{.}}</li>{{/fixes}}'+
                    '</ul><hr>'+
                    '<p>'+
                    '   And a lot of other stuff, see the'+
                    '   <a href="https://github.com/devsnd/cherrymusic/blob/{{version}}/CHANGES" target="_blank">'+
                    '   CHANGELOG</a>.'+
                    '</p>',
                    {
                        version: resp.data.version,
                        features: resp.data.features,
                        features_count: resp.data.features.length,
                        feature_title: resp.data.features.length > 1 ? 'features' : 'feature',
                        fixes: resp.data.fixes,
                        fixes_count: resp.data.fixes.length,
                        fixes_title: resp.data.fixes.length > 1 ? 'fixes' : 'fix',
                    });
                $('#motd').html(html);
            } else if(resp.type == 'wisdom'){
                $('#motd').html('useless wisdom<hr>'+resp.data);
            } else {
                window.console.error('unknown motd type '+resp.type);
            }
        },
        errorFunc('could not fetch message of the day')
    );
}

/***
ON DOCUMENT READY... STEADY... GO!
***/
var playlistManager;
$(document).ready(function(){
    "use strict";
    $('#playlistBrowser').hide();
    loadConfig(function(){
        playlistManager = new PlaylistManager();
        $('#username-label').text('('+loggedInUserName+')');
    });
    loadUserOptions(function(){
        initKeyboardshortcuts();
        dontCloseWindowIfMusicPlays();
        $('#albumart').toggle(userOptions.ui.display_album_art)
    });
    $('#search-panel').on('scroll', function(){
        //enable loading of images when in viewport
        MediaBrowser.static.albumArtLoader('#search-panel');
    });

    //register top level directories
    $('div#progressscreen').fadeOut('slow');
    //window.setInterval("resizePlaylistSlowly()",2000);
    $('#searchform .searchinput').focus();
    sendHeartBeat();
    displayMessageOfTheDay();
    $('#adminpanel').on('shown.bs.modal', function (e) {
        updateUserList();
    });
    $('#save-playlist-from-queue').on('click',function(){
        $('#playlisttitle').val('');
        $("#playlistpublic").attr("checked", true);
    });
    $('#saveplaylistmodal').on('shown.bs.modal',function(){
        $('#playlisttitle').focus();
        $('#playlisttitle').bind('keyup',function(e){
            if(e.which === 13) { //enter
                savePlaylistAndHideDialog();
            } else if(e.which === 27){ //escape
                $('#saveplaylistmodal').modal('hide');
            }
        });
    });
    $('#saveplaylistmodal').on('hide', function(){
        $('#playlisttitle').unbind('keyup');
    });

    $('#changeAlbumArt').on('shown.bs.modal', function(){
        //empty old search results
        $('#changeAlbumArt .coverart-tryout').empty();
        //set input field in modal
        $("#albumart-search-term").val(decodeURIComponent($('#changeAlbumArt').attr('data-dirname')));
        $("#albumart-search-term").focus();
        //when pressing enter, the search should start:
        $("#albumart-search-term").off('keypress').on('keypress', function(e){
            if (e.keyCode == '13' || e.which == '13'){
                searchAlbumArt();
            }
        });
    });

    $('#changePassword').on('show.bs.modal', function(){
        //$('#changePassword').data('modal').options.focusOn = '#oldpassword-change';
    });
    userOptionCheckboxListener('#misc-show_playlist_download_buttons',
                               'misc.show_playlist_download_buttons');
    userOptionCheckboxListener('#misc-autoplay_on_add',
                               'misc.autoplay_on_add');
    userOptionCheckboxListener('#ui-confirm_quit_dialog',
                               'ui.confirm_quit_dialog');
    userOptionCheckboxListener('#ui-display_album_art',
                               'ui.display_album_art');
    userOptionMultivalListener("select[name='media-force_transcode_to_bitrate']",
                                'media.force_transcode_to_bitrate');
    $('#media-force_transcode_to_bitrate-disable').click(function(){
        optionSetter('media.force_transcode_to_bitrate', 0, function(){
            $('#media-force_transcode_to_bitrate-disable').closest('.error').hide();
        });
    });
    $('#ui-display_album_art').click(function() {
        $('#albumart').toggle($('#ui-display_album_art').prop('checked'));
    });
});
