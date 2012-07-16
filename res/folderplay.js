/** minified jquery color plugin **/
(function(d){d.each(["backgroundColor","borderBottomColor","borderLeftColor","borderRightColor","borderTopColor","color","outlineColor"],function(f,e){d.fx.step[e]=function(g){if(!g.colorInit){g.start=c(g.elem,e);g.end=b(g.end);g.colorInit=true}g.elem.style[e]="rgb("+[Math.max(Math.min(parseInt((g.pos*(g.end[0]-g.start[0]))+g.start[0]),255),0),Math.max(Math.min(parseInt((g.pos*(g.end[1]-g.start[1]))+g.start[1]),255),0),Math.max(Math.min(parseInt((g.pos*(g.end[2]-g.start[2]))+g.start[2]),255),0)].join(",")+")"}});function b(f){var e;if(f&&f.constructor==Array&&f.length==3){return f}if(e=/rgb\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*\)/.exec(f)){return[parseInt(e[1]),parseInt(e[2]),parseInt(e[3])]}if(e=/rgb\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*\)/.exec(f)){return[parseFloat(e[1])*2.55,parseFloat(e[2])*2.55,parseFloat(e[3])*2.55]}if(e=/#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})/.exec(f)){return[parseInt(e[1],16),parseInt(e[2],16),parseInt(e[3],16)]}if(e=/#([a-fA-F0-9])([a-fA-F0-9])([a-fA-F0-9])/.exec(f)){return[parseInt(e[1]+e[1],16),parseInt(e[2]+e[2],16),parseInt(e[3]+e[3],16)]}if(e=/rgba\(0, 0, 0, 0\)/.exec(f)){return a.transparent}return a[d.trim(f).toLowerCase()]}function c(g,e){var f;do{f=d.curCSS(g,e);if(f!=""&&f!="transparent"||d.nodeName(g,"body")){break}e="backgroundColor"}while(g=g.parentNode);return b(f)}var a={aqua:[0,255,255],azure:[240,255,255],beige:[245,245,220],black:[0,0,0],blue:[0,0,255],brown:[165,42,42],cyan:[0,255,255],darkblue:[0,0,139],darkcyan:[0,139,139],darkgrey:[169,169,169],darkgreen:[0,100,0],darkkhaki:[189,183,107],darkmagenta:[139,0,139],darkolivegreen:[85,107,47],darkorange:[255,140,0],darkorchid:[153,50,204],darkred:[139,0,0],darksalmon:[233,150,122],darkviolet:[148,0,211],fuchsia:[255,0,255],gold:[255,215,0],green:[0,128,0],indigo:[75,0,130],khaki:[240,230,140],lightblue:[173,216,230],lightcyan:[224,255,255],lightgreen:[144,238,144],lightgrey:[211,211,211],lightpink:[255,182,193],lightyellow:[255,255,224],lime:[0,255,0],magenta:[255,0,255],maroon:[128,0,0],navy:[0,0,128],olive:[128,128,0],orange:[255,165,0],pink:[255,192,203],purple:[128,0,128],violet:[128,0,128],red:[255,0,0],silver:[192,192,192],white:[255,255,255],yellow:[255,255,0],transparent:[255,255,255]}})(jQuery);


function submitsearch(){
    $('div#progressscreen').fadeIn('fast');
    var searchfor = $('#searchfield input').val();
    $.ajax({
        //url: "index.php",
        
        context: $(this),
        data: {
            'action' : 'search',
            'value' : searchfor
            },
        success: function(data){
            $('#searchresults').html(data);
            registerlistdirs($('#searchresults').find('ul'));
            registercompactlistdirs($('#searchresults').find('ul'));
			registermp3s($('#searchresults').find('ul'));
            $('div#progressscreen').fadeOut('fast');
        }
    });
    return false;
}

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
					//url: "index.php",
                    
					context: $(this),
					data: {
						'action' : 'listdir',
						'value' : directory
						},
					success: function(data){
						$(this).parent().append(data);
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
                                        //url: "index.php",
                                        
                                        context: $(this),
                                        data: {
                                                'action' : 'compactlistdir',
                                                'value' : directory,
						'filter' : filter
                                                },
                                        success: function(data){
                                                $(this).parent().append(data);
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

$(document).ready(function(){
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

$('#searchfield .button').click(submitsearch);

$('.save-playlist').click(function(){
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

});

addSong = function(path,title){
        mediaPlaylist.add({
	    title: title,
	    mp3: path
    });
    pulseTab('jplayer');
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