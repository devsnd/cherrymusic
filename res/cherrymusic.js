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

/***
RENDERING
***/
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
                html += listify(renderCompact(e.label,e.urlpath));
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
function renderCompact(label,filterpath, filter){
    //compact
    return '<a dir="'+filepath+'" filter="'+filter+'" href="javascript:;" class="compactlistdir">'+filter.upper()+'</a>'
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
        swfPath: "js",
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


/*$('.save-playlist').click(function(){
		tracks = []
		$.each(mediaPlaylist.playlist, function(i,v) {
			tracks.push(mediaPlaylist.playlist[i].mp3);
			//alert(mediaPlaylist.playlist[i].mp3);
		});
		tracksstring = tracks.join(';');
		$.ajax({
                                        //url: "index.php",
                                        
                                        context: $(this),
                                        data: {
                                                'action' : 'saveplaylist',
                                                'value' : tracksstring
                                                },
                                        success: function(data){
						alert('playlist was saved! '+data);
                                        }
                });

	});


$('.load-playlist').click(function(){
	var playlistname = $(this).html();
	alert(playlistname);
	$.ajax({
		url: "index.php",
		context: $(this),
		data: {
			'action' : 'loadplaylist',
			'value' : playlistname
		},
		success: function(data){
			mediaPlaylist.playlist = []
			mediaPlaylist.original = []
			mediaPlaylist._refresh();
			var newplaylist = data.split('\\n');
			for(var i in newplaylist){
				var filename = newplaylist[i].split('/');
				filename = filename[filename.length-1];
				addSong(newplaylist[i],filename);
			}
		}
	});
});
*/

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
        $('div.tabs ul.tabNavigation a').removeClass('selected');
        $(this).addClass('selected');
        return false;
    });//.filter(':first').click();
});

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
ON DOCUMENT READY... STEADY... GO!
***/
$(document).ready(function(){
    fetchMessageOfTheDay();
    initJPlayer();
    $('#searchfield .button').click(submitsearch);



});