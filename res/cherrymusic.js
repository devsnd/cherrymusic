//
// CherryMusic - a standalone music server
// Copyright (c) 2012 Tom Wallroth & Tilman Boerner
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
    var encoderPreferenceOrder = ['ogg','mp3'];
}

var availableEncoders = undefined;
var availablejPlayerFormats = ['mp3','ogg'];
var availableDecoders = undefined;
var transcodingEnabled = undefined;
var userOptions = undefined;
var isAdmin = undefined;
var loggedInUserName = undefined;
var REMEMBER_PLAYLIST_INTERVAL = 3000;
var HEARTBEAT_INTERVAL_MS = 30*1000;

var playlistSelector = '.jp-playlist';

var executeAfterConfigLoaded = []

function api(data_or_action, successfunc, errorfunc, background){
    "use strict";
    if(!successfunc){
        successfunc = function(){};
    }
    var completefunc;
    if(background){
        completefunc = function(){};
    } else {
        completefunc = function(){$('div#progressscreen').fadeOut('fast')};
    }
    var senddata;
    var apiaction;
    if(typeof data_or_action === "string"){
        apiaction = data_or_action;
        senddata = {};
    } else {
        apiaction = data_or_action['action'];
        senddata = {"value" :  data_or_action['value'] };

    }
    var errorFuncWrapper = function(errorFunc){
        return function(httpstatus){
            if(httpstatus.status == 401){
                reloadPage();
            }
            errorFunc();
        }
    }
    var defaultErrorHandler = function(){
        errorFunc('calling API function "'+apiaction+'"')();
        $('div#progressscreen').fadeOut('fast');
    };
    if(!errorfunc){
        errorfunc = errorFuncWrapper(defaultErrorHandler);
    } else {
        errorfunc = errorFuncWrapper(errorfunc);
    }
    if(!background){
        $('div#progressscreen').fadeIn('fast');
    }
    var urlaction = '/api';
    if(apiaction){
        urlaction += '/'+apiaction;
    }
    $.ajax({
        url: urlaction,
        context: $(this),
        type: 'POST',
        data: senddata,
        success: successfunc,
        error: errorfunc,
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
        displayNotification(msg,'error');
    };
}
function successNotify(msg){
    return function(){
        displayNotification(msg,'success');
    };
}

function renderUserMessage(msg, type){
    return Mustache.render([
        '<div class="alert {{cssclass}}">',
            '<button type="button" class="close" data-dismiss="alert">',
                '&times;',
            '</button>',
            '{{msg}}',
        '</div>',
    ].join(''),
    {
        msg : msg,
        cssclass: type=='error'?'alert-error':type=='success'?'alert-success':''
    });
}

function displayNotification(msg,type){
    $('#errormessage').html(renderUserMessage(msg,type));
}
function removeError(msg){
    if($('#errormessage').html() == renderUserMessage(msg,'error')){
        $('#errormessage').html('');
    }
}
/*******************
CONFIGURATION LOADER
*******************/
function loadConfig(){
    "use strict";
    var data = {
        'action' : 'getconfiguration',
    };
    var success = function(data){
        var dictatedClientConfig = jQuery.parseJSON(data);
        availableEncoders = dictatedClientConfig.getencoders;
        availableDecoders = dictatedClientConfig.getdecoders;
        transcodingEnabled = dictatedClientConfig.transcodingenabled;
        isAdmin = dictatedClientConfig.isadmin;
        loggedInUserName = dictatedClientConfig.username;
        for(var i=0; i<executeAfterConfigLoaded.length; i++){
            executeAfterConfigLoaded[i]();
        }
        if(!isAdmin){
            $('a[href="#adminpanel"]').hide();
        }
    };
    var error = errorFunc("Could not fetch client configuration, CherryMusic will not work. Clearing the browser cache might help.");
    api(data,success,error,true);
}

/************
 * USER OPTIONS
 * **********/

function loadUserOptions(onSuccess){
    var success = function(data){
        userOptions = jQuery.parseJSON(data);
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
        
        $('#pldlbutton').attr('checked',userOptions.misc.show_playlist_download_buttons);
    }
    api('getuseroptions',success);
}

function loadAndShowUserOptions(){
    loadUserOptions(function(){
        $('#useroptions').fadeIn();
    });
}

var optionSetter = function(name,val,success,error){
    api(
            {
                action:'setuseroption',
                value:JSON.stringify(
                    {
                        'optionkey':name,
                        'optionval':val
                    }
                )
            },
            function(){success(); loadUserOptions();},
            error
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
            $('#shortcut-changer input').unbind('keyup',keydownhandler);
            $('html').unbind('keyup',keydownhandler);
            $('#shortcut-changer').fadeOut('fast');
        }
        if(e.which !== 27 && e.which !== 32){ //do not bind escape / space
            optionSetter(option,e.which,keyboardsetterend,keyboardsetterend)();
        }
        keyboardsetterend();
    }
    $('#shortcut-changer input').bind('keyup',keydownhandler);
    $('html').bind('keyup',keydownhandler);
}

function reloadStylesheets() {
    var queryString = '?reload=' + new Date().getTime();
    $('link[rel="stylesheet"]').each(function () {
        if(this.href.indexOf('api/customcss.css') != -1){
            this.href = this.href.replace(/\?.*|$/, queryString);
        }
    });
}
/***
SEARCH
***/
function fastsearch(append){
    "use strict";
    var data = {
        'action' : 'fastsearch',
        'value' : $('#searchfield input').val()
    };
    var success = function(data){
        if(append){
            $('#searchresults').append(parseAndRender(data));
        } else {
            $('#searchresults').html(parseAndRender(data));
        }
        registerlistdirs($('#searchresults').find('ul'));
        registercompactlistdirs($('#searchresults').find('ul'));
        registermp3s($('#searchresults').find('ul'));
        $('#searchresults').find('ul').append('<li class="slowsearch">loading more search results...</li>');
    };
    var error = function(){
        errorFunc('failed loading fast-search results')();
    };
    api(data,success,error);
    return false;
}
function search(append){
    "use strict";
    var data = {
        'action' : 'search',
        'value' : $('#searchfield input').val()
    };
    var success = function(data){
        if(append){
            $('#searchresults').append(parseAndRender(data));
        } else {
            $('#searchresults').html(parseAndRender(data));
        }
        registerlistdirs($('#searchresults').find('ul'));
        registercompactlistdirs($('#searchresults').find('ul'));
        registermp3s($('#searchresults').find('ul'),false);
        $('#searchresults').find('ul li.slowsearch').remove();
    };
    var error = function(){
        errorFunc('failed loading search results')();
    };
    api(data,success,error);
    return false;
}
function submitsearch(){
    search();
    return false;
}

/********
RENDERING
********/
function parseAndRender(data){
    "use strict";
    return renderList(jQuery.parseJSON(data));
}
function renderList(l){
    "use strict";
    var html = "";
    $.each(l, function(i, e) {
        html+=Mustache.render([
            '{{#isfile}}',
                '<li class="fileinlist">',
                    '<a title="{{label}}" href="javascript:;" class="mp3file" path="{{fileurl}}">',
                        '<span class="fullpathlabel">',
                            '{{fullpath}}',
                        '</span>',
                        '{{label}}',
                    '</a>',
                '</li>',
            '{{/isfile}}',
            '{{#isdir}}',
                '<li>',
                    '<a dir="{{dirpath}}" href="javascript:;" class="listdir">',
                        '{{^isrootdir}}',
                                '{{{coverartfetcher}}}',
                        '{{/isrootdir}}',
                        '<div class="listdir-name-wrap">',
                            '<span class="listdir-name">{{dirpath}}<span>',
                        '</div>',
                    '</a>',
                '</li>',
            '{{/isdir}}',
            '{{#iscompact}}',
                '<li>',
                   '<a dir="{{filepath}}" filter="{{filter}}" href="javascript:;" class="compactlistdir">',
                        '{{filterUPPER}}',
                    '</a>',
                '</li>',
            '{{/iscompact}}',
            ].join(''),
            {
                isfile: e.type == 'file',
                label: e.label,
                fullpath: e.path,
                fileurl : e.urlpath,
                
                isdir: e.type == 'dir',
                dirpath: e.path,
                isrootdir: e.path && !e.path.indexOf('/')>0,
                coverartfetcher: function(){
                    return renderCoverArtFetcher(encodeURIComponent(JSON.stringify({'directory' : e.path})))
                },
                
                iscompact: e.type == 'compact',
                filepath: e.urlpath,
                filter: e.label,
                filterUPPER: e.label.toUpperCase(),
            });
    });
    if(html==""){
        html += '<li><div style="text-align: center">Nothing found. Sorry.</div></li>'
    }
    return '<ul>'+html+'</ul>';
}

function renderCoverArtFetcher(searchterms){
    return ['<div class="albumart-display unloaded" search-data="'+searchterms+'">',
    '<img src="/res/img/folder.png" width="80" height="80" />',
    '</div>'].join('');
}

function albumArtLoader(){
    var winpos = $(window).height()+$(window).scrollTop();
    $('.albumart-display.unloaded').each(
        function(idx){
            if($(this).position().top < winpos){
               $(this).find('img').attr('src', '/api/fetchalbumart/'+$(this).attr('search-data'));
               $(this).removeClass('unloaded');
            }
        }
    );
}
    
/***
INTERACTION
***/
listdirclick = function(mode){
        "use strict";
        var directory = $(this).attr("dir");
        if($(this).siblings('ul').length>0){
            if($(this).siblings('ul').is(":visible")){
                $(this).siblings('ul').slideUp('slow');
            } else {
                $(this).siblings('ul').slideDown('slow');
            }
        } else {
            //$('div#progressscreen').fadeIn('fast');
            var data = {
                'action' : 'listdir',
                'value' : JSON.stringify({ 'directory' : directory })
            };
            var currdir = this;
            var success = function(data){
                $(currdir).parent().append(parseAndRender(data));
                registerlistdirs($(currdir).parent().find('ul'));
                registercompactlistdirs($(currdir).parent().find('ul'));
                registermp3s($(currdir).parent().find('ul'));
                $(currdir).siblings("ul").hide().slideDown('fast');
                albumArtLoader();
            };
            api(data,success,errorFunc('unable to list directory'));
        }
};
compactlistdirclick = function(){
    "use strict";
    var directory = $(this).attr("dir");
    var filter = $(this).attr("filter");
    //alert(directory);
    if($(this).siblings('ul').length>0){
        if($(this).siblings('ul').is(":visible")){
            $(this).siblings('ul').slideUp('slow');
        } else {
            $(this).siblings('ul').slideDown('slow');
        }
    } else {
        var data = {
            'action' : 'compactlistdir',
            'value' : JSON.stringify({ 'directory' : directory,
                        'filter' : filter })
        };
        var currdir = this;
        var success = function(data){
            $(currdir).parent().append(parseAndRender(data));
            registerlistdirs($(currdir).parent().find('ul'));
            registercompactlistdirs($(currdir).parent().find('ul'));
            registermp3s($(currdir).parent().find('ul'));
            $(currdir).siblings("ul").slideDown('slow');
            albumArtLoader();
        };
        api(data,success,errorFunc('unable to list compact directory'));
    }

};
registerlistdirs = function(parent){
    "use strict";
    $(parent).find("a.listdir").click(
        listdirclick
    );
};

registercompactlistdirs = function(parent){
    "use strict";
    $(parent).find("a.compactlistdir").click(
        compactlistdirclick
    );
};

addAllToPlaylist = function($source, plid){
    "use strict";
    $source.siblings('li').find('.mp3file').each(function(){
        playlistManager.addSong( $(this).attr("path"), $(this).attr("title"), plid );
    });
    $(this).blur();
    return false;
};
addThisTrackToPlaylist = function(){
    playlistManager.addSong( $(this).attr("path"), $(this).attr("title") );
    $(this).blur();
    return false;
}

registermp3s = function(parent,mode, playlistlabel){
    "use strict";
    if(typeof mode === 'undefined'){
        mode = 'addPlayAll';
    }
    var foundMp3 = $(parent).find(".mp3file").click(
        addThisTrackToPlaylist
    ).html();
    if(foundMp3){
        var editplaylist = playlistManager.getEditingPlaylist();
        switch(mode) {
            case 'loadPlaylist':
                $(parent).prepend('<a class="addAllToPlaylist" href="javascript:;">load playlist</a>');
                $(parent).children('.addAllToPlaylist').click( function() {
                    var pl = playlistManager.newPlaylistNoShow([], playlistlabel);
                    addAllToPlaylist($(this), pl.id);
                    pl.saved = true;
                    playlistManager.showPlaylist(pl.id);
                    $(this).blur();
                    return false;
                });
                 break;
            case 'addPlayAll':
                var playlistname  = typeof editplaylist === 'undefined' ? 'undefined playlist' : editplaylist.name;
                $(parent).prepend('<a class="addAllToPlaylist" href="javascript:;"><b>+</b> add all to <span class="plsmgr-editingplaylist-name">' + playlistname + '</span></a>');
                $(parent).children('.addAllToPlaylist').click( function() {
                    addAllToPlaylist($(this));
                    $(this).blur();
                    return false;
                });
                break;
            default:
                break;
        }
    }
}

updateLibrary = function(){
    api('updatedb')
}

function showAlbumArtChangePopOver(jqobj){
    jqobj.popover({selector: jqobj.siblings('img'), title: 'Change cover art', html: true, content: '<img src="/res/img/folder.png" /><img src="/res/img/folder.png" /><img src="/res/img/folder.png" />'});
}


/* PLAYLIST CREATION AND MANAGEMENT END*/

ext2jPlayerFormat = function(ext){
    switch(ext){
        case "mp3": return "mp3";

        case "ogg":
        case "oga": return "oga";

        case "m4a":
        case "mp4":
        case "aac": return "m4a";
        
        case "flac" : return "flac"

        case "wav": return "wav";

        case "weba": return "webma";
    }
}


/**********
TRANSCODING
**********/

function getTranscodePath(filepath, format){
    "use strict";
    var match = filepath.match(/\/serve(.*)$/);
    if(match){
        return "/trans"+match[1]+"/get."+format;
    }
}

/******************
PLAYLIST MANAGEMENT
******************/
function savePlaylistAndHideDialog(){
    "use strict";
    var name = $('#playlisttitle').val();
    var pub = $('#playlistpublic').attr('checked')?true:false;
    if(name.trim() !== ''){
        var pl = playlistManager.newPlaylistFromQueue();
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
    var data = { 'action':'saveplaylist',
                'value':JSON.stringify({
                            'playlist':pl.jplayerplaylist.playlist,
                            'public':ispublic,
                            'playlistname':playlistname,
                            'overwrite':overwrite,
                        })
                };
    var success = function(){
        playlistManager.getPlaylistById(plid).name = playlistname;
        playlistManager.getPlaylistById(plid).public = ispublic;
        playlistManager.getPlaylistById(plid).saved = true;
        playlistManager.refresh();
        playlistManager.showPlaylist(plid);
    }
    api(data,success,errorFunc('error saving playlist'));
}
function getAddrPort(){
    m = (window.location+"").match(/https?:\/\/(.+?):?(\d+).*/);
    return 'http://'+m[1]+':'+m[2];
}

function ord(c)
{
  return c.charCodeAt(0);
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

function showPlaylists(){
    "use strict";
    var success = function(data){
            var addressAndPort = getAddrPort();
            var pls = '<ul>';
            $.each($.parseJSON(data),function(i,e){
                pls += Mustache.render([
                '<li id="playlist{{playlistid}}">',
                    '<div class="remoteplaylist">',
                        '<div class="playlisttitle">',
                            '<a href="javascript:;" onclick="loadPlaylist({{playlistid}}, \'{{playlistlabel}}\')">',
                            '{{playlistlabel}}',
                            '</a>',
                        '</div>',
                    
                        '{{#isowner}}',
                            '<div class="ispublic">',
                                '<span class="label {{publiclabelclass}}">',
                                    '{{publicorprivate}}',
                                    '<input onchange="changePlaylist({{playlistid}},\'public\',$(this).is(\':checked\'))" type="checkbox" {{publicchecked}}>',
                                    '</span>',
                            '</div>',
                        '{{/isowner}}',                   
                        
                        '{{{usernamelabel}}}',
                        
                        '{{#candelete}}',
                            '<div class="deletebutton">',
                                '<a href="javascript:;" class="btn btn-mini btn-danger" onclick="confirmDeletePlaylist({{playlistid}}, \'{{playlistlabel}}\')">x</a>',
                            '</div>',
                        '{{/candelete}}',
                        
                        '{{#showdownloadbuttons}}',
                            '<div class="dlbutton">',
                                '<a class="btn btn-mini" href="/api/downloadpls?value={{dlval}}">',
                                '&darr;&nbsp;PLS',
                                '</a>',
                            '</div>',
                            '<div class="dlbutton">',
                                '<a class="btn btn-mini" href="/api/downloadm3u?value={{dlval}}">',
                                '&darr;&nbsp;M3U',
                                '</a>',
                            '</div>',
                        '{{/showdownloadbuttons}}',
                        
                    '</div>',
                    '<div class="playlistcontent">',
                    '</div>',
                '</li>'
                ].join(''),
                    {
                    playlistid: e['plid'],
                    isowner: e.owner,
                    candelete: e.owner || isAdmin, 
                    showdownloadbuttons: userOptions.misc.show_playlist_download_buttons,
                    playlistlabel:e['title'],
                    dlval : JSON.stringify({ 'plid' : e['plid'],
                        'addr' : addressAndPort
                        }),
                    username: e['username'],
                    usernamelabel: renderUserNameLabel(e['username']),
                    publicchecked: e['public'] ? 'checked="checked"' : '',
                    publicorprivate: e['public'] ? 'public' : 'private',
                    publiclabelclass : e['public'] ? 'label-success' : 'label-info',
                    }
                );
            });
            pls += '</ul>';
            $('.available-playlists').html(pls);
            $('.hideplayliststab').slideDown('fast');
            $('.showplayliststab').slideUp('fast');
            $('.available-playlists').slideDown();
        };

    var error = errorFunc('error loading external playlists');

    api('showplaylists',success,error);
}

renderUserNameLabel = function(username){
    return Mustache.render([
        '<div class="usernamelabel">',
            '<span class="badge" style="background-color: {{hexcolor}}">',
                '{{username}}',
            '</span>',
        '</div>'
    ].join(''),
    {
        hexcolor: userNameToColor(username),
        username: username,
    }
    );
}

function changePlaylist(plid,attrname,value){
    window.console.log(plid);
    window.console.log(attrname);
    window.console.log(value);
    api(
        {
            action:'changeplaylist',
            value: JSON.stringify({
                    'plid' : plid,
                    'attribute' : attrname,
                    'value' : value
                    }),
        },
        function(){
            showPlaylists();
        },
        errorFunc('error changing playlist attribute')
    );
}

function confirmDeletePlaylist(id,title){
    $('#deletePlaylistConfirmButton').off();
    $('#deletePlaylistConfirmButton').on('click', function(){
        api({action:'deleteplaylist', value: id},false,errorFunc('error deleting playlist'));
        $('#dialog').fadeOut('fast');
        showPlaylists();
    });
    $('#deleteplaylistmodalLabel').html(Mustache.render('Really delete Playlist "{{title}}"',{title:title}));
    $('#deleteplaylistmodal').modal('show');
}

function hidePlaylists(){
    "use strict";
    $('.showplayliststab').slideDown('fast');
    $('.hideplayliststab').slideUp('fast');
    $('.available-playlists').slideUp();
}
function loadPlaylist(playlistid, playlistlabel){
    "use strict";
    var pldomid = "#playlist"+playlistid+' .playlistcontent';

    if('' === $(pldomid).html().trim()){
        var data = {'action':'loadplaylist',
                    'value': playlistid };
        var success = function(data){
            $(pldomid).hide();
            $(pldomid).append(parseAndRender(data));
            $(pldomid).slideDown('slow');
            registermp3s($(pldomid).find('ul'), 'loadPlaylist', playlistlabel);
        };
        api(data,success,errorFunc('error loading external playlist'))
    } else {
        $(pldomid).slideToggle('slow');
    }
}



var lastPlaylistHeight = 0;
function resizePlaylistSlowly(){
    var currentHeight = $('.jp-playlist').height();
    if(lastPlaylistHeight <= currentHeight){
        $('#jp-playlist-wrapper').animate({'min-height': currentHeight});
    }
    lastPlaylistHeight = currentHeight;
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
    var success = reloadPage;
    api('logout',success);
}


/***
ADMIN PANEL
***/

function updateUserList(){
    "use strict";
    var success = function(data){
        var htmllist = "";
        var response = $.parseJSON(data);
        var time = response['time'];
        $.each(response['userlist'],function(i,e){           
            var reltime = time - e.last_time_online;
            htmllist += Mustache.render([
                '<li {{#isadmin}}class="admin"{{/isadmin}}>',
                    '<div class="row-fluid">',
                        '<div class="span1">',
                            '<span class="badge ',
                                '{{#isonline}}badge-success{{/isonline}}',
                                '{{^isonline}}badge-important{{/isonline}}',
                                '">&#x2022;',
                            '</span>',
                        '</div>',
                        '<div class="span4">{{{usernamelabel}}}</div>',
                        '<div class="span5"> last seen: {{fuzzytime}}</div>',
                        '<div class="span2">',
                            '{{#isdeletable}}',
                                '<a class="btn btn-mini btn-danger" href="javascript:;" onclick="userDelete({{userid}})">delete</a>',
                            '{{/isdeletable}}',
                        '</div>',
                    '</div>',
                '</li>',
            ].join(''),{
                isadmin: e.admin,
                isdeletable: e.deletable,
                userid: e.id,
                isonline: reltime < HEARTBEAT_INTERVAL_MS/500,
                usernamelabel: renderUserNameLabel(e.username),
                fuzzytime: time2text(reltime),
            });
        });
        $('#adminuserlist').html(htmllist);
    };
    api('getuserlist',success,errorFunc('cannot fetch user list'));
}
function addNewUser(){
    "use strict";
    var newusername = $('#newusername').val();
    var newpassword = $('#newpassword').val();
    var newisadmin = $('#newisadmin').attr('checked')?1:0;
    if(newusername.trim() === '' || newpassword.trim() === ''){
        return;
    }
    var data = {'action':'adduser',
                'value' : JSON.stringify({
                    'username':newusername,
                    'password':newpassword,
                    'isadmin':newisadmin
                })};
    var success = function(data){
        $('#newusername').val('');
        $('#newpassword').val('');
        $('#newisadmin').prop('checked', false);
        updateUserList();
    };
    api(data,success,errorFunc('failed to add new user'));
}

function userDelete(userid){
    var data = {'action':'userdelete',
                'value' : JSON.stringify({
                    'userid':userid
                })};
    var success = function(data){
        updateUserList();
    };
    api(data,success,errorFunc('failed to delete user'));
}
function userChangePassword(){
    if (! validateNewPassword($('#newpassword-change'), $('#repeatpassword-change'))) {
        return false;
    }
    var data = {'action':'userchangepassword',
                'value' : JSON.stringify({
                    'oldpassword':$('#oldpassword-change').val(),
                    'newpassword':$('#newpassword-change').val()
                })};
    $('#oldpassword-change').val('');
    var success = function(data){
        $('#changePassword').find('input').each(function(idx, el) { $(el).val(''); } )
        $('#changePassword').modal('hide');
        $('#userOptions').modal('hide');
        successNotify('Password changed successfully!')();
    };
    api(data,success,errorFunc('failed to change password'));
}
function validateNewPassword($newpwfield, $repeatpwfield){
    var newpw = $newpwfield.val();
    var repeatpw = $repeatpwfield.val();
    if (newpw == repeatpw) {
        $repeatpwfield.closest('.control-group').removeClass('error')
        return true;
    }
    $repeatpwfield.closest('.control-group').addClass('error')
    return false;
}

function enableJplayerDebugging(){
    $('#jplayer_inspector').jPlayerInspector({jPlayer:$('#jquery_jplayer_1'),visible:true});
    $('#jquery_jplayer_1').data().jPlayer.options.errorAlerts = true;
    $('#jquery_jplayer_1').data().jPlayer.options.warningAlerts = true;
    $('#jplayer_inspector_update_0').click();
}
/***
MESSAGE OF THE DAY
***/
function fetchMessageOfTheDay(){
    "use strict";
    var success = function(data){
        $('#oneliner').text(data);
    };
    api('getmotd', success, errorFunc('could not fetch message of the day'));
}

function loadBrowserIfEmpty(){
    "use strict";
    if('' === $('#browser').html().trim()){
        loadBrowser();
    }
}

function loadBrowser(){
    var data = { 'action' : 'listdir' };
    var success = function(data){
        $('#searchresults').html(parseAndRender(data));
        registerlistdirs($('#searchresults').find('ul'));
        registercompactlistdirs($('#searchresults').find('ul'));
        registermp3s($('#searchresults').find('ul'));
    };
    api(data,success,errorFunc('failed to load file browser'));
}
var origcolors = {};
function pulse(selector){
    "use strict";
    var elem = $(selector);
    if(typeof origcolors[selector] === 'undefined'){
        origcolors[selector] = elem.css('background-color');
    }
    elem.stop(true, true);
    elem.animate({backgroundColor: '#ffffff'+' !important'},100);
    elem.animate({backgroundColor: origcolors[selector]+' !important'},100);
    elem.animate({backgroundColor: '#ffffff'+' !important'},100);
    elem.animate({backgroundColor: origcolors[selector]+' !important'},100);
    elem.animate({backgroundColor: '#ffffff'+' !important'},100);
    elem.animate({backgroundColor: origcolors[selector]+' !important'},100);
}

/***
HELPER
***/

function reload(){
    "use strict";
    window.location = "http://"+window.location.host;
}
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
/********************
STYLE TRANSFORMATIONS
*********************/
//returns the size of the browser window
function viewport() {
    var e = window, a = 'inner';
    if ( !( 'innerWidth' in window ) ){
        a = 'client';
        e = document.documentElement || document.body;
    }
    return { width : e[ a+'Width' ] , height : e[ a+'Height' ] }
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
    var years = parseInt(months/12);
    var t='';
    if(abssec < 30){
        return 'just now'
    } else {
        if(years != 0){
            years+' years';
            if(years > 20){
                return 'never';
            }
        } else if(months != 0){
            t = months+' months';
        } else if(weeks != 0){
            t = weeks+' weeks';
        } else if(days != 0){
            t = days+' days';
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
    var focusedElement = $("*:focus");
    var inputFieldFocused = focusedElement.length > 0;
    if(inputFieldFocused){
        if(e.which === 27){ //escape -> unfocus
            focusedElement.blur();
        }
    } else {
        var actions = { 'next' :    function(e){playlistManager.cmd_next()},
                        'pause' :   function(e){playlistManager.cmd_pause()},
                        'play' :    function(e){playlistManager.cmd_play()},
                        'prev' :    function(e){playlistManager.cmd_previous()},
                        'search' :  function(e){$('#searchform input').focus().select(); e.preventDefault();},
                        'stop' :    function(e){playlistManager.cmd_stop()},
                        };
        for(var action in actions){
            if(e.which === userOptions.keyboard_shortcuts[action]){
                window.console.log('triggering: '+action);
                actions[action](e);
            }
        }
        if(e.which === 32){
            window.console.log('triggering: pause');
            actions['pause']();
        }
    }
}

function sendHeartBeat(){
    api('heartbeat',
        function(){ removeError('connection to server lost')},
        errorFunc('connection to server lost'),
        true)
}

function enableMobileSwiping(){
    var wrap = $('.swipe-panels>div');
    var width = wrap.width();
    var sp = $('.search-panel').get(0);
    var pp = $('.playlist-panel').get(0);
    //set up css rules for swiping:
    $('body').css('overflow','hidden');
    $('body').css('height','100%');
    $('html').css('height','100%');
    $('.search-panel').css('position', 'absolute');
    $('.search-panel').css('top', '165px');
    $('.search-panel').css('left', '0');
    $('.playlist-panel').css('position', 'absolute');
    $('.playlist-panel').css('top', '165px');
    $('.playlist-panel').css('left', '100%');
    var leftoffset = 0;
    $('body')
    .on('movestart', function(e) {
        leftoffset = $('.search-panel').hasClass('active-swipe')? 0 : -100;
        width = wrap.width();
        // If the movestart heads off in a upwards or downwards
        // direction, prevent it so that the browser scrolls normally.
        if ((e.distX > e.distY && e.distX < -e.distY) ||
            (e.distX < e.distY && e.distX > -e.distY)) {
            e.preventDefault();
            return;
        }
    })
    .on('move', function(e){
        var left = 100 * e.distX / width;
        if (e.distX < 0) {
            sp.style.left = (leftoffset+left) + '%';
            sp.style.width = (100-leftoffset+left) + '%';
            pp.style.left = (leftoffset+left+100)+'%';
        }
        if (e.distX > 0) {
            sp.style.left = (leftoffset+left) + '%';
            pp.style.left = (leftoffset+left+100)+'%';
        }
    })
    .on('moveend', function(e) {
       if(parseInt(pp.style.left) < 50){
           $('.search-panel').animate({left: '-100%'});
           $('.playlist-panel').animate({left: '0%'});
           $('.search-panel').removeClass('active-swipe');
           $('.playlist-panel').addClass('active-swipe');
       } else {
            $('.search-panel').animate({left: '0%'});
            $('.playlist-panel').animate({left: '100%'});
            $('.search-panel').addClass('active-swipe');
            $('.playlist-panel').removeClass('active-swipe');
       }
    });
}
function disableMobileSwiping(){
    $('body').off('movestart').off('move').off('moveend');
    $('.search-panel').removeAttr('style');
    $('.playlist-panel').removeAttr('style');
    $('body').removeAttr('style');
    $('html').removeAttr('style');
}

/***
ON DOCUMENT READY... STEADY... GO!
***/
var playlistManager;
$(document).ready(function(){
    "use strict";
    //initTabs();
    $('#playlistBrowser').hide();
    fetchMessageOfTheDay();
    $('#searchfield .bigbutton').click(submitsearch);
    $('.hideplaylisttab').hide();
    executeAfterConfigLoaded.push(function(){ playlistManager = new PlaylistManager() });
    executeAfterConfigLoaded.push(function(){ $('#username-label').text('('+loggedInUserName+')') });
    loadConfig();
    loadUserOptions(initKeyboardshortcuts);
    //register top level directories
	registerlistdirs($("html").get());
	registercompactlistdirs($("html").get());
	$('div#progressscreen').fadeOut('slow');
    window.setInterval("resizePlaylistSlowly()",2000);
    $('#searchform .searchinput').focus();
    sendHeartBeat();
    window.setInterval("sendHeartBeat()",HEARTBEAT_INTERVAL_MS);
    $('#adminpanel').on('shown', function (e) {
        updateUserList();
    });
    $('#saveplaylistmodal').on('shown',function(){
        $('#playlisttitle').focus();
        $('#playlisttitle').val('');
        $('#playlistpublic').attr('checked', true);
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
    $('#pldlbutton').on('change',function(){
        optionSetter(   'misc.show_playlist_download_buttons',
                        $(this).attr('checked')=='checked',
                        function(){
                            $(this).attr('checked',userOptions.misc.show_playlist_download_buttons)
                        },
                        errorFunc('Error setting option!')
        );
    });
    //enable loading of images when in viewport
    window.onscroll = albumArtLoader;
    //enableMobileSwiping();
});
