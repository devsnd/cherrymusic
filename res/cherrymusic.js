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

/***
SEARCH
***/
function submitsearch(){
    $('div#progressscreen').fadeIn('fast');
    var searchfor = $('#searchfield input').val();
    $.ajax({      
        url: '/api',
        context: $(this),
        data: {
            'action' : 'search',
            'value' : searchfor
            },
        success: function(data){
            $('#searchresults').html(parseAndRender(data));
            registerlistdirs($('#searchresults').find('ul'));
            registercompactlistdirs($('#searchresults').find('ul'));
			registermp3s($('#searchresults').find('ul'));
            $('div#progressscreen').fadeOut('fast');
        },
        error: function(){
            alert("I'm sorry, but this is an error message...\n\nIt indicates an error... *sigh*\nSorry, it's just... my whole purpose of existance is to give bad news.\nIt's frustrating.\nWould you mind just clicking 'ok' and leave me alone?");
            $('div#progressscreen').fadeOut('fast');
        }
    });
    return false;
}

/********
RENDERING
********/
function parseAndRender(data){
    return renderList(jQuery.parseJSON(data));
}
function renderList(l){
    html = "";
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
                alert('Error parsing server response!');
                break;
        }
    });
    return ulistify(html);
}
function renderDir(label,urlpath,dirpath){
    return '<a dir="'+dirpath+'" href="javascript:;" class="listdir">'+dirpath+'</a>';
}
function renderFile(label,urlpath,dirpath){
            atitle = 'title="'+label+'"'
            ahref = 'href="javascript:;"'
            cssclass = ' class="mp3file" '
            apath = 'path="'+urlpath+'"'
            fullpathlabel = '<span class="fullpathlabel">'+dirpath+'</span>'
            return '<a '+atitle+' '+ahref+' '+apath+' '+cssclass+'>'+fullpathlabel+label+'</a>'
}
function renderCompact(label,filepath, filter){
    //compact
    return '<a dir="'+filepath+'" filter="'+filter+'" href="javascript:;" class="compactlistdir">'+filter.toUpperCase()+'</a>'
}
function listify(html, classes){
    if(!classes){classes='';}
    return '<li '+classes+'>'+html+'</li>'
}
function ulistify(html){
    return '<ul>'+html+'</ul>';
}
/***
INTERACTION
***/
$(function(){
	listdirclick = function(mode){
			var directory = $(this).attr("dir");
			if($(this).siblings('ul').length>0){
				if($(this).siblings('ul').is(":visible")){
					$(this).siblings('ul').slideUp('slow');
				} else {
					$(this).siblings('ul').slideDown('slow');
				}
			} else {
				$('div#progressscreen').fadeIn('fast');
				$.ajax({
					url: "/api",
                    
					context: $(this),
					data: {
						'action' : 'listdir',
						'value' : directory
						},
					success: function(data){
						$(this).parent().append(parseAndRender(data));
						registerlistdirs($(this).parent().find('ul'));
						registercompactlistdirs($(this).parent().find('ul'));
						registermp3s($(this).parent().find('ul'));
						$(this).siblings("ul").slideDown('slow');
						$('div#progressscreen').fadeOut('fast');
					}
				});
			}
	}
	compactlistdirclick = function(){
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
				$('div#progressscreen').fadeIn('fast');

				$.ajax({                       
                        context: $(this),
                        url: '/api',
                        data: {
                                'action' : 'compactlistdir',
                                'value' : directory,
                                'filter' : filter
                        },
                        success: function(data){
                                $(this).parent().append(parseAndRender(data));
                                registerlistdirs($(this).parent().find('ul'));
                                registercompactlistdirs($(this).parent().find('ul'));
                                registermp3s($(this).parent().find('ul'));
                                $(this).siblings("ul").slideDown('slow');
                                $('div#progressscreen').fadeOut('fast');
                        }
                });
			}

	}
	registerlistdirs = function(parent){ 
		$(parent).find("a.listdir").click(
			listdirclick
		);
	}

	registercompactlistdirs = function(parent){
		$(parent).find("a.compactlistdir").click(
	        	compactlistdirclick
                );
        }

	addAllToPlaylist = function(){
		//alert($(this).siblings('ul').html());
		$(this).siblings('li').find('.mp3file').each(function(){
			addSong( $(this).attr("path"), $(this).attr("title") );
		});

	}

	registermp3s = function(parent){
		var foundMp3 = $(parent).find(".mp3file").click(
			function(){
				addSong( $(this).attr("path"), $(this).attr("title") );
			}
		).html();
		if(foundMp3){
			$(parent).prepend('<a class="addAllToPlaylist" href="javascript:;">add All to Playlist</a>');
			$(parent).children('.addAllToPlaylist').click(
				addAllToPlaylist
			)
		}
	}

	//register top level directories
	registerlistdirs($("html").get());
	registercompactlistdirs($("html").get());
	$('div#progressscreen').fadeOut('slow');
});

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
		 errorAlerts: false,
		 warningAlerts: false
        });
    }
}

addSong = function(path,title){
        mediaPlaylist.add({
	    title: title,
	    mp3: path
    });
    pulseTab('jplayer');
}
clearPlaylist = function(){
    mediaPlaylist.remove();
    rememberPlaylist();
}

function showPlaylistSaveDialog(){
    $('#dialog input').val('');
    $('#dialog').fadeIn('fast');
}

function savePlaylistAndHideDialog(){
    var name = $('#playlisttitle').val();
    var pub = $('#playlistpublic').attr('checked')?true:false;
    if(name.trim() != ''){
        savePlaylist(name,pub);
        $('#dialog').fadeOut('fast')
    }
}

function savePlaylist(playlistname,ispublic){
    $.ajax({
        url: '/api',
        type: 'POST',
        data: { 'action':'saveplaylist',
                'value':JSON.stringify(
                    {
                    'playlist':mediaPlaylist.playlist,
                    'public':ispublic,
                    'playlistname':playlistname}
                    )
        },
        success:function(data){
            
        },
        error:function(){
            alert('error');
        }
    });
}
function showPlaylists(){
    $.ajax({
        url: '/api',
        type: 'POST',
        data: { 'action':'showplaylists' },
        success:function(data){
            var pls = '<ul>';
            $.each($.parseJSON(data),function(i,e){
                pls += '<li>';
                var onclick = "loadPlaylist('"+e[0]+"')";
                pls += '<a class="remoteplaylist" href="javascript:;" onclick="'+onclick+'">'
                pls += e[1]+'</a></li>';
            });
            pls += '</ul>';
            $('.available-playlists').html(pls);
            $('.hideplayliststab').slideDown('fast');
            $('.showplayliststab').slideUp('fast');
            $('.available-playlists').slideDown();
            
        },
        error:function(){
            alert('error');
        }
    });
}
function hidePlaylists(){
    $('.showplayliststab').slideDown('fast');
    $('.hideplayliststab').slideUp('fast');
    $('.available-playlists').slideUp();
}
function loadPlaylist(playlistname){
    $.ajax({
        url: '/api',
        type: 'POST',
        data: { 'action':'loadplaylist',
                'value': playlistname
        },
        success:function(data){
            $.each($.parseJSON(data),function(i,e){
                addSong(e.mp3,e.title);
            });
        },
        error:function(){
            alert('error');
        }
    });
}

function rememberPlaylistPeriodically(lastlen){
    if (mediaPlaylist.playlist.length != lastlen){
        /* save playlist in session */
         $.ajax({
            url: '/api',
            type: 'POST',
            data: { 'action':'rememberplaylist',
                    'value':JSON.stringify({'playlist':mediaPlaylist.playlist})
            },
            success:function(data){
                
            },
            error:function(){
                alert('error rememebering playlist.');
            }
        });
    }
    // check every second if the playlist changed 
    window.setTimeout("rememberPlaylistPeriodically("+mediaPlaylist.playlist.length+")",1000);
}

function restorePlaylist(){
    /*restore playlist from session*/
    $.ajax({
        url: '/api',
        type: 'POST',
        data: { 'action':'restoreplaylist'},
        success:function(data){
            $.each($.parseJSON(data),function(i,e){
                addSong(e.mp3,e.title);
            });
        },
        error:function(){
            alert('error');
        }
    });
}


function logout(){
    $.ajax({
        url: '/api',
        type: 'POST',
        data: { 'action':'logout',
        },
        success:function(data){
            reload()
        },
        error:function(){
            alert('error');
        }
    });
}
/***
ADMIN PANEL
***/
function toggleAdminPanel(){
    var panel = $('#adminpanel');
    if(panel.is(":visible")){
        panel.slideUp();
    } else {
        updateUserList();
        panel.slideDown();
    }
}
function updateUserList(){
     $.ajax({
        url: '/api',
        type: 'POST',
        data: { 'action':'getuserlist' },
        success:function(data){
            var htmllist = ""
            $.each($.parseJSON(data),function(i,e){
                if(e.admin){
                    htmllist += '<li class="admin">'
                } else {
                    htmllist += '<li>'
                }
                htmllist += e.id+' - '+e.username+'</li>';
            });
            $('#adminuserlist').html(htmllist)
        },
        error:function(){
            alert('error');
        }
    });
}
function addNewUser(){
    var newusername = $('#newusername').val();
    var newpassword = $('#newpassword').val();
    var newisadmin = $('#chkSelect').attr('checked')?true:false;
    if(newusername.trim() == '' || newpassword.trim() == ''){
        return;
    }
     $.ajax({
        url: '/api',
        type: 'POST',
        data: { 'action':'adduser',
                'value' : JSON.stringify({
                        'username':newusername,
                        'password':newpassword,
                        'isadmin':newisadmin
                        })
                
        },
        success:function(data){
            updateUserList();
        },
        error:function(){
            alert('error');
        }
    });
}

/***
MESSAGE OF THE DAY
***/
function fetchMessageOfTheDay(){
    $.ajax({
        url: "/api",
        context: $(this),
        data: { 'action' : 'getmotd' },
                success: function(data){
                    $('#oneliner').html(data);
                }
    });
}

/**
TAB FUNCTIONALITY
**/
function showTab(tabid){
    $('div.tabs '+tabid).show();
}
function hideAllTabs(){
    $('div.tabs > div').each(function(){
            $(this).hide();
    });
}

$(function () {
    hideAllTabs();
    showTab('#search');
    $('div.tabs ul.tabNavigation a').click(function () {
        $("html").scrollTop(0);
        hideAllTabs();
        showTab(this.hash);
        if('#browser' == this.hash){
            loadBrowserIfEmpty();
        }
        $('div.tabs ul.tabNavigation a').removeClass('selected');
        $(this).addClass('selected');
        return false;
    });//.filter(':first').click();
});

function loadBrowserIfEmpty(){
    if('' == $('#browser').html().trim()){
        $('div#progressscreen').fadeIn('fast');
        $.ajax({
        url: "/api",
        context: $(this),
        data: { 'action' : 'listdir' },
        success: function(data){
            $('#browser').html(parseAndRender(data));
            registerlistdirs($('#browser').find('ul'));
            registercompactlistdirs($('#browser').find('ul'));
            registermp3s($('#browser').find('ul'));
            $('div#progressscreen').fadeOut('fast');
        },
        error: function(){
            $('div#progressscreen').fadeOut('fast');
        }
        });
    }
}

$(document).ready(function(){
    origcolor = $('div.tabs ul.tabNavigation .jplayer').css('background-color');
});
function pulseTab(tabname){
    var elem = $('div.tabs ul.tabNavigation .'+tabname);
    elem.stop(true, true)
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
    window.location = "http://"+window.location.host;
}

/***
ON DOCUMENT READY... STEADY... GO!
***/
$(document).ready(function(){
    fetchMessageOfTheDay();
    initJPlayer();
    $('#searchfield .bigbutton').click(submitsearch);
    $('.hideplaylisttab').hide();
    restorePlaylist();
    rememberPlaylistPeriodically(0);
});