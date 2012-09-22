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
var playableExtensions = [];
var REMEMBER_PLAYLIST_INTERVAL = 3000;

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

function loadConfig(){
    "use strict";
    var success = function(data){
        playableExtensions = jQuery.parseJSON(data);
    };
    var error = errorFunc('Failed loading configuration');
    api('getplayables',success,error);
}

/***
SEARCH
***/
function submitsearch(){
    "use strict";
    var data = {
        'action' : 'search',
        'value' : $('#searchfield input').val()
    };
    var success = function(data){
        $('#searchresults').html(parseAndRender(data));
        registerlistdirs($('#searchresults').find('ul'));
        registercompactlistdirs($('#searchresults').find('ul'));
        registermp3s($('#searchresults').find('ul'));
    };
    var error = function(){
        errorFunc('failed loading search results')();
    };
    api(data,success,error);
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
            })+'<a class="floatright" href="javascript:;">&uarr;DIR</a>';
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
            api(data,success);
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
        api(data,success);
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

registermp3s = function(parent){
    "use strict";
    var foundMp3 = $(parent).find(".mp3file").click(
        function(){
            addSong( $(this).attr("path"), $(this).attr("title") );
        }
    ).html();
    if(foundMp3){
        $(parent).prepend('<a class="addAllToPlaylist" href="javascript:;">add All to Playlist</a>');
        $(parent).children('.addAllToPlaylist').click(
            addAllToPlaylist
        );
    }
};

/***
JPLAYER FUNCTIONS
***/
function initJPlayer(){
    if (typeof mediaPlaylist === 'undefined') {
	mediaPlaylist = new jPlayerPlaylist({
        jPlayer: "#jquery_jplayer_1",
        cssSelectorAncestor: "#jp_container_1"
	}, [], {
		playlistOptions: {
			enableRemoveControls: true
		},
        swfPath: "res/js",
		solution: "flash,html",
		preload: 'metadata',
        supplied: "mp3",
        wmode: "window",
        errorAlerts: false
        });
    }
}

addSong = function(path,title){
    "use strict";
    mediaPlaylist.add({
        title: title,
        mp3: path
    });
    pulseTab('jplayer');
};
clearPlaylist = function(){
    "use strict";
    mediaPlaylist.remove();
};

function showPlaylistSaveDialog(){
    "use strict";
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
    api(data);
}
function showPlaylists(){
    "use strict";
    var success = function(data){
            var pls = '<ul>';
            $.each($.parseJSON(data),function(i,e){
                pls += Mustache.render(
                    ['<li>',
                    '<a class="remoteplaylist" onclick="loadPlaylist({{playlistid}})" href="javascript:;">',
                    '{{playlistlabel}}',
                    '</a>',
                    '<a class="exportPLS button" href="/api?action=downloadpls&value={{playlistid}}">',
                    '&darr; PLS',
                    '</a>',
                    '<a class="exportM3U button" href="/api?action=downloadm3u&value={{playlistid}}"">',
                    '&darr; M3U',
                    '</a>',
                    '</li>'].join(''),
                {
                playlistid:e[0],
                playlistlabel:e[1]
                });
            });
            pls += '</ul>';
            $('.available-playlists').html(pls);
            $('.hideplayliststab').slideDown('fast');
            $('.showplayliststab').slideUp('fast');
            $('.available-playlists').slideDown();
        };
    var error = function(){
            alert('error');
    };
    api('showplaylists',success,error);
}

function hidePlaylists(){
    "use strict";
    $('.showplayliststab').slideDown('fast');
    $('.hideplayliststab').slideUp('fast');
    $('.available-playlists').slideUp();
}
function loadPlaylist(playlistname){
    "use strict";
    var data = {'action':'loadplaylist',
                'value': playlistname };
    var success = function(data){
        $.each($.parseJSON(data),function(i,e){
            addSong(e.mp3,e.title);
        });
    };
    api(data,success)
}

function rememberPlaylistPeriodically(lastlen){
    "use strict";
    if (mediaPlaylist.playlist && mediaPlaylist.playlist.length !== lastlen){
        /* save playlist in session */
        var data = {'action':'rememberplaylist',
                    'value':JSON.stringify(
                        {'playlist':mediaPlaylist.playlist}
                    )};
        var error = errorFunc('cannot rememebering playlist: failed to connect to server.');
        api(data, false, error, true);
    }
    // check every second if the playlist changed
    var currentLength = mediaPlaylist.playlist ? mediaPlaylist.playlist.length : 0;
    window.setTimeout("rememberPlaylistPeriodically("+currentLength+")",REMEMBER_PLAYLIST_INTERVAL);
}

function restorePlaylist(){
    "use strict";
    /*restore playlist from session*/
    var success = function(data){
            $.each($.parseJSON(data),function(i,e){
                addSong(e.mp3,e.title);
            });
    };
    var error = function(){
            alert('error');
    };
    api('restoreplaylist',success,error);
}

function removePlayedFromPlaylist(){
    if(mediaPlaylist.current != 0){
        if(!mediaPlaylist.removing){
            mediaPlaylist.remove(0);
        }
        window.setTimeout(removePlayedFromPlaylist,50);
    }
}

function logout(){
    "use strict";
    var success = function(data){ reload(); };
    api('logout',success);
}

function displayCurrentSong(){
    if(mediaPlaylist.playlist.length>0){
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
    api('getuserlist',success);
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
    api(data,success);
}

/***
MESSAGE OF THE DAY
***/
function fetchMessageOfTheDay(){
    "use strict";
    var success = function(data){
        $('#oneliner').html(data);
    };
    api('getmotd', success);
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
        api(data,success);
    }
}

origcolor = '#000000';
$(document).ready(function(){
    "use strict";
    origcolor = $('div.tabs ul.tabNavigation .jplayer').css('background-color');
});
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

var viewStyle = 'single';
function switchView(style){
    if(!style){
        if('single' == viewStyle){
            
        }
    }
    if('single' == style){
        
    } else if('sidebyside' == style){
        $('#jplayer').css('width','50%');
        $('#jplayer').css('float','right');
        $('#jplayer').css('display','block');
        $('#jplayer').css('margin-top','36px');
        $('#search').css('width','50%');
        $('#search').css('float','left');
        $('#search').css('display','block');
    }
}




/***
ON DOCUMENT READY... STEADY... GO!
***/
$(document).ready(function(){
    "use strict";
    initTabs();
    fetchMessageOfTheDay();
    initJPlayer();
    $('#searchfield .bigbutton').click(submitsearch);
    $('.hideplaylisttab').hide();
    restorePlaylist();
    loadConfig();
    rememberPlaylistPeriodically(0);
    //register top level directories
	registerlistdirs($("html").get());
	registercompactlistdirs($("html").get());
	$('div#progressscreen').fadeOut('slow');
    window.setInterval("displayCurrentSong()", 1000)
});