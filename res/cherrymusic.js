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
var playableExtensions = undefined;
var availableEncoders = undefined;
var availablejPlayerFormats = [];
var availableDecoders = undefined;
var transcodingEnabled = undefined;
var REMEMBER_PLAYLIST_INTERVAL = 3000;

var playlistSelector = '.jp-playlist';

var executeAfterConfigLoaded = []

function api(data_or_action, successfunc, errorfunc, background){
    "use strict";
    if(!errorfunc){
        errorfunc = errorFunc();
    }
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
    if(typeof data_or_action === "string"){
        senddata = {"action" : data_or_action};
    } else {
        senddata = data_or_action;
    }
    if(!background){
        $('div#progressscreen').fadeIn('fast');
    }
    $.ajax({      
        url: '/api',
        context: $(this),
        type: 'POST',
        data: senddata,
        success: successfunc,
        error: errorfunc,
        complete: completefunc,
    });
}

function errorFunc(msg){
    "use strict";
    if(msg){
        return function(){
            window.alert('ERROR: '+msg+" :'(");
        };
    } else {
        return function(){
            window.alert("I'm sorry, but this is an error message...\n\nIt indicates an error... *sigh*\nSorry, it's just... my whole purpose of existance is to give bad news.\nIt's frustrating.\nWould you mind just clicking 'ok' and leave me alone?");
        };
    }
}
/*******************
CONFIGURATION LOADER
*******************/
function loadConfig(){
    "use strict";
    var success = function(data){
        playableExtensions = jQuery.parseJSON(data);
        configCompletionHandler();
    };
    var error = errorFunc('Failed loading configuration for playable extensions!');
    api('getplayables',success,error, true);
    
    success = function(data){
        availableEncoders = jQuery.parseJSON(data);
        configCompletionHandler();
    };
    error = errorFunc('Failed loading configuration for available Encoders!');
    api('getencoders',success,error, true);
    
    success = function(data){
        availableDecoders = jQuery.parseJSON(data);
        configCompletionHandler();
    };
    error = errorFunc('Failed loading configuration for available Decoders!');
    api('getdecoders',success,error, true);
    
    success = function(data){
        transcodingEnabled = jQuery.parseJSON(data);
        configCompletionHandler();
    };
    error = errorFunc('Failed loading configuration value "transcodingenabled"!');
    api('transcodingenabled',success,error, true);
}

function configCompletionHandler(){
    if( playableExtensions != undefined
        availableEncoders != undefined
        availableDecoders != undefined
        transcodingEnabled != undefined
    ){
        for(var i=0; i<executeAfterConfigLoaded.length; i++){
            executeAfterConfigLoaded[i]();
        }
    }
}

/***
SEARCH
***/
function fastsearch(append=false){
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
        search(true);
    };
    var error = function(){
        errorFunc('failed loading fast-search results')();
    };
    api(data,success,error);
    return false;
}
function search(append=false){
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
        registermp3s($('#searchresults').find('ul'),addPlayAll=false);
    };
    var error = function(){
        errorFunc('failed loading search results')();
    };
    api(data,success,error);
    return false;
}
function submitsearch(){
    fastsearch();
    $('#searchresults').find('ul').append('<li>More search results</li>');
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
        switch(e.type){
            case 'file':
                html += listify(renderFile(e.label,e.urlpath,e.path),'class="fileinlist"');
                break;
            case 'dir':
                html += listify(renderDir(e.label,e.urlpath,e.path));
                break;
            case 'compact':
                html += listify(renderCompact(e.label,e.urlpath,e.label));
                break;
            default:
                errorFunc('server response is not valid!')();
                break;
        }
    });
    return ulistify(html);
}
function renderDir(label,urlpath,dirpath){
    "use strict";
    return '<a dir="'+dirpath+'" href="javascript:;" class="listdir">'+dirpath+'</a>';
}
function renderFile(label,urlpath,dirpath){
    "use strict";
    var fullpathlabel = Mustache.render('<span class="fullpathlabel">{{fpdirpath}}</span>',{fpdirpath:dirpath});
    if(isPlayableAudioFile(urlpath)){
        return Mustache.render('<a title="{{atitle}}" href="{{ahref}}" class="{{acssclass}}" path="{{apath}}">{{{afullpathlabel}}} {{alabel}}</a>', {
                atitle : label,
                alabel: label,
                ahref : 'javascript:;',
                acssclass : 'mp3file',
                apath : urlpath,     
                afullpathlabel : fullpathlabel,            
            });//+'<a class="floatright" href="javascript:;">&uarr;DIR</a>';
    } else {
        return '<span>'+fullpathlabel+label+'</span>';
    }
}
function renderCompact(label,filepath, filter){
    "use strict";
    return '<a dir="'+filepath+'" filter="'+filter+'" href="javascript:;" class="compactlistdir">'+filter.toUpperCase()+'</a>';
}
function listify(html, classes){
    "use strict";
    if(!classes){classes='';}
    return '<li '+classes+'>'+html+'</li>';
}
function ulistify(html){
    "use strict";
    return '<ul>'+html+'</ul>';
}
function isPlayableAudioFile(filePath){
    "use strict";
    for(var i=0; i<playableExtensions.length; i++){
        if(endsWith( filePath.toUpperCase(),
                     playableExtensions[i].toUpperCase())){
            return true;
        }
    }
    return false;
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
                'value' : directory
            };
            var currdir = this;
            var success = function(data){
                $(currdir).parent().append(parseAndRender(data));
                registerlistdirs($(currdir).parent().find('ul'));
                registercompactlistdirs($(currdir).parent().find('ul'));
                registermp3s($(currdir).parent().find('ul'));
                $(currdir).siblings("ul").slideDown('slow');
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
            'value' : directory,
            'filter' : filter
        };
        var currdir = this;
        var success = function(data){
            $(currdir).parent().append(parseAndRender(data));
            registerlistdirs($(currdir).parent().find('ul'));
            registercompactlistdirs($(currdir).parent().find('ul'));
            registermp3s($(currdir).parent().find('ul'));
            $(currdir).siblings("ul").slideDown('slow');
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

addAllToPlaylist = function(){
    "use strict";
    $(this).siblings('li').find('.mp3file').each(function(){
        addSong( $(this).attr("path"), $(this).attr("title") );
    });
};

registermp3s = function(parent,addPlayAll=true){
    "use strict";
    var foundMp3 = $(parent).find(".mp3file").click(
        function(){
            addSong( $(this).attr("path"), $(this).attr("title") );
        }
    ).html();
    if(foundMp3 && addPlayAll){
        $(parent).prepend('<a class="addAllToPlaylist" href="javascript:;">add All to Playlist</a>');
        $(parent).children('.addAllToPlaylist').click(
            addAllToPlaylist
        );
    }
};

/***
JPLAYER FUNCTIONS
***/
function setAvailableJPlayerFormats(){
    for(var i=0; i<availableEncoders.length; i++){
        availablejPlayerFormats.push(ext2jPlayerFormat(availableEncoders[i]));
    }
    sortFormatPreferrencePerBrowser();
}

function sortFormatPreferrencePerBrowser(){
    var browser = detectBrowser();
    //see http://www.w3schools.com/html/html5_audio.asp for available formats per browser
    if(['msie','safari'].indexOf(browser) != -1){
    //set preferred format for IE and safari to mp3
        if(availableEncoders.indexOf('mp3') != -1){
            //remove mp3
            availableEncoders = availableEncoders.filter(function(i){return i!='mp3'});
            //add mp3 as first playback format
            availableEncoders.unshift('mp3');
        }
    } else {
        //set to ogg for all te others
        if(availableEncoders.indexOf('ogg') != -1){
            //remove ogg
            availableEncoders = availableEncoders.filter(function(i){return i!='ogg'});
            //add ogg as first playback format
            availableEncoders.unshift('ogg');
        }
    }
}

function initJPlayer(){
    if (typeof mediaPlaylist === 'undefined') {
	mediaPlaylist = new jPlayerPlaylist({
        jPlayer: "#jquery_jplayer_1",
        cssSelectorAncestor: "#jp_container_1"
	}, [], {
		playlistOptions: {
			enableRemoveControls: true,
            playlistSelector: playlistSelector,
		},
        swfPath: "res/js",
		solution: "html",
		preload: 'metadata',
        supplied: availablejPlayerFormats.join(),
        wmode: "window",
        errorAlerts: false
        });
    }
}

ext2jPlayerFormat = function(ext){
    switch(ext){
        case "mp3": return "mp3";
        
        case "ogg": 
        case "oga": return "oga";
        
        case "m4a": 
        case "mp4":
        case "aac": return "m4a";
        
        case "wav": return "wav";
        
        case "weba": return "webma";
    }
}

addSong = function(path,title){
    "use strict";
    var ext = getFileTypeByExt(path);
    var track = {
        title: title,
    }
    //add natively supported path
    track[ext2jPlayerFormat(ext)] = path;
    
    if(transcodingEnabled){
        //add transcoded paths
        for(var i=0; i<availableEncoders.length; i++){
            var enc = availableEncoders[i];
            if(enc !== ext){
                track[ext2jPlayerFormat(enc)] = getTranscodePath(path,enc);
            }
        }
    }
    
    mediaPlaylist.add(track);
    pulseTab('jplayer');
    var success = function(data){
        var metainfo = $.parseJSON(data)
        track.duration = metainfo.length
        mediaPlaylist._refresh(true);
    }
    api({action:'getsonginfo',
        value: path}, success, errorFunc('error getting song metainfo'), true);
};
clearPlaylist = function(){
    "use strict";
    mediaPlaylist.remove();
};
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
function showPlaylistSaveDialog(){
    "use strict";
    $('#dialog').html(
    ['<p>Please enter a Name for this Playlist:</p>',
    '<input type="text" id="playlisttitle" />',
    'public:<input type="checkbox" checked="checked" id="playlistpublic" />',
    '<a class="button" href="javascript:;" onclick="savePlaylistAndHideDialog()">Save</a>',
    '<a class="button" href="javascript:;" onclick="$(\'#dialog\').fadeOut(\'fast\')">Close</a>'].join(''));

    $('#dialog input').val('');
    $('#dialog').fadeIn('fast');
}

function savePlaylistAndHideDialog(){
    "use strict";
    var name = $('#playlisttitle').val();
    var pub = $('#playlistpublic').attr('checked')?true:false;
    if(name.trim() !== ''){
        savePlaylist(name,pub);
        $('#dialog').fadeOut('fast');
    }
}

function savePlaylist(playlistname,ispublic){
    "use strict";
    var data = { 'action':'saveplaylist',
                'value':JSON.stringify({
                            'playlist':mediaPlaylist.playlist,
                            'public':ispublic,
                            'playlistname':playlistname
                        })
                };
    api(data,false,errorFunc('error saving playlist'));
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
                pls += Mustache.render(
                    ['<li id="playlist{{playlistid}}">',
                    '<div class="remoteplaylist">',
                        '<div class="playlisttitle">',
                            '<a href="javascript:;" onclick="loadPlaylist({{playlistid}})">',
                            '{{playlistlabel}}',
                            '</a>',
                        '</div>',
                        '<div class="usernamelabel">',
                            '<span style="background-color: {{usernamelabelcolor}}" >{{username}}</span>',
                        '</div>',
            			'<div class="deletebutton">',
			            '<a href="javascript:;" class="button" onclick="confirmDeletePlaylist({{playlistid}})">x</a>',
            			'</div>',
                        '<div class="dlbutton">',
                            '<a class="exportPLS button" href="/api?action=downloadpls&value={{dlval}}">',
                            '&darr; PLS',
                            '</a>',
                        '</div>',
                        '<div class="dlbutton">',
                            '<a class="exportM3U button" href="/api?action=downloadm3u&value={{dlval}}">',
                            '&darr; M3U',
                            '</a>',
                        '</div>',
                    '</div>',
                    '<div class="playlistcontent">',
                    '</div>',
                    '</li>'].join(''),
                {
                playlistid:e['plid'],
                playlistlabel:e['title'],
                dlval : JSON.stringify({ 'plid' : e['plid'],
                    'addr' : addressAndPort
                    }),
                username: e['username'],
                usernamelabelcolor: userNameToColor(e['username']),
                });
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

function confirmDeletePlaylist(id){
    $('#dialog').html(['<p>Do you really want to delete this precious playlist?</p>',
    '<a class="button" href="javascript:;" onclick="deletePlaylistAndHideDialog('+id+')">Yes, get it out of my life</a>',
    '<a class="button" href="javascript:;" onclick="$(\'#dialog\').fadeOut(\'fast\')">No, leave it as it is</a>'].join(''));
    $('#dialog').fadeIn('fast');
}

function deletePlaylistAndHideDialog(id){
    api({action:'deleteplaylist', value: id},false,errorFunc('error deleting playlist'));
    $('#dialog').fadeOut('fast');
    showPlaylists();
}

function hidePlaylists(){
    "use strict";
    $('.showplayliststab').slideDown('fast');
    $('.hideplayliststab').slideUp('fast');
    $('.available-playlists').slideUp();
}
function loadPlaylist(playlistid){
    "use strict";
    var pldomid = "#playlist"+playlistid+' .playlistcontent';
    
    if('' === $(pldomid).html().trim()){
        var data = {'action':'loadplaylist',
                    'value': playlistid };
        var success = function(data){
            $(pldomid).hide();
            $(pldomid).append(parseAndRender(data));
            $(pldomid).slideDown('slow');
            registerlistdirs($(pldomid).find('ul'));
            registercompactlistdirs($(pldomid).find('ul'));
            registermp3s($(pldomid).find('ul'));
        };
        api(data,success,errorFunc('error loading external playlist'))
    } else {
        $(pldomid).slideToggle('slow');
    }
}

var lastPlaylist;
function rememberPlaylistPeriodically(){
    "use strict";
    if (mediaPlaylist.playlist && lastPlaylist !== JSON.stringify(mediaPlaylist.playlist)){
        /* save playlist in session */
        var data = {'action':'rememberplaylist',
                    'value':JSON.stringify(
                        {'playlist':mediaPlaylist.playlist}
                    )};
        var error = errorFunc('cannot rememebering playlist: failed to connect to server.');
        var success = function(){
            lastPlaylist = JSON.stringify(mediaPlaylist.playlist)
        }
        api(data, success, error, true);
    }
}

function restorePlaylistAndRememberPeriodically(){
    "use strict";
    /*restore playlist from session*/
    var success = function(data){
            mediaPlaylist.playlist = $.parseJSON(data);
            mediaPlaylist._refresh(true);
    };
    api('restoreplaylist',success,errorFunc('error restoring playlist'));
        window.setInterval("rememberPlaylistPeriodically()",REMEMBER_PLAYLIST_INTERVAL );
}

function removePlayedFromPlaylist(){
    if(mediaPlaylist.current != 0){
        if(!mediaPlaylist.removing){
            mediaPlaylist.remove(0);
        }
        window.setTimeout(removePlayedFromPlaylist,50);
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

function logout(){
    "use strict";
    var success = function(data){ reload(); };
    api('logout',success);
}

function displayCurrentSong(){
    if(mediaPlaylist && mediaPlaylist.playlist && mediaPlaylist.current && mediaPlaylist.playlist.length>0){
        $('.cm-songtitle').html(mediaPlaylist.playlist[mediaPlaylist.current].title);
    } else {
        $('.cm-songtitle').html('');
    }
}
/***
ADMIN PANEL
***/
function toggleAdminPanel(){
    "use strict";
    var panel = $('#adminpanel');
    if(panel.is(":visible")){
        panel.slideUp();
    } else {
        updateUserList();
        panel.slideDown();
    }
}
function updateUserList(){
    "use strict";
    var success = function(data){
        var htmllist = "";
        $.each($.parseJSON(data),function(i,e){
            if(e.admin){
                htmllist += '<li class="admin">';
            } else {
                htmllist += '<li>';
            }
            htmllist += e.id+' - '+e.username+'</li>';
        });
        $('#adminuserlist').html(htmllist);
    };
    api('getuserlist',success,errorFunc('cannot fetch user list'));
}
function addNewUser(){
    "use strict";
    var newusername = $('#newusername').val();
    var newpassword = $('#newpassword').val();
    var newisadmin = $('#chkSelect').attr('checked')?1:0;
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
        updateUserList();
    };
    api(data,success,errorFunc('failed to add new user'));
}

/***
MESSAGE OF THE DAY
***/
function fetchMessageOfTheDay(){
    "use strict";
    var success = function(data){
        $('#oneliner').html(data);
    };
    api('getmotd', success, errorFunc('could not fetch message of the day'));
}

/**
TAB FUNCTIONALITY
**/
function showTab(tabid){
    "use strict";
    $('div.tabs '+tabid).show();
}
function hideAllTabs(){
    "use strict";
    $('div.tabs > div').each(function(){
            $(this).hide();
    });
}

function initTabs() {
    "use strict";
    hideAllTabs();
    showTab('#search');
    $('div.tabs ul.tabNavigation a').click(function () {
        $("html").scrollTop(0);
        hideAllTabs();
        showTab(this.hash);
        if('#browser' === this.hash){
            loadBrowserIfEmpty();
        }
        $('div.tabs ul.tabNavigation a').removeClass('selected');
        $(this).addClass('selected');
        return false;
    });
    saveOriginalTabColor();
}

function loadBrowserIfEmpty(){
    "use strict";
    if('' === $('#browser').html().trim()){
        var data = { 'action' : 'listdir' };
        var success = function(data){
            $('#browser').html(parseAndRender(data));
            registerlistdirs($('#browser').find('ul'));
            registercompactlistdirs($('#browser').find('ul'));
            registermp3s($('#browser').find('ul'));
        };
        api(data,success,errorFunc('failed to load file browser'));
    }
}

origcolor = '#000000';
function saveOriginalTabColor(){
    "use strict";
    origcolor = $('div.tabs ul.tabNavigation .jplayer').css('background-color');
}

function pulseTab(tabname){
    "use strict";
    var elem = $('div.tabs ul.tabNavigation .'+tabname);
    elem.stop(true, true);
    elem.animate({backgroundColor: '#ffffff'},100);
    elem.animate({backgroundColor: origcolor},100);
    elem.animate({backgroundColor: '#ffffff'},100);
    elem.animate({backgroundColor: origcolor},100);
    elem.animate({backgroundColor: '#ffffff'},100);
    elem.animate({backgroundColor: origcolor},100);
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
    var browsers = ['firefox','msie','chrome','safari','midori']
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

/***
ON DOCUMENT READY... STEADY... GO!
***/
$(document).ready(function(){
    "use strict";
    initTabs();
    fetchMessageOfTheDay();
    $('#searchfield .bigbutton').click(submitsearch);
    $('.hideplaylisttab').hide();
    executeAfterConfigLoaded.push(restorePlaylistAndRememberPeriodically);
    executeAfterConfigLoaded.push(setAvailableJPlayerFormats);
    executeAfterConfigLoaded.push(initJPlayer);
    loadConfig();
    //register top level directories
	registerlistdirs($("html").get());
	registercompactlistdirs($("html").get());
	$('div#progressscreen').fadeOut('slow');
    window.setInterval("displayCurrentSong()", 1000);
    window.setInterval("resizePlaylistSlowly()",2000);
    $('#searchform .searchinput').focus();
    $(playlistSelector+" ul").sortable({
        update: function(e,ui){
            mediaPlaylist._reorderByDomElements();
            }
        });
	$(playlistSelector+" ul").disableSelection();
});
