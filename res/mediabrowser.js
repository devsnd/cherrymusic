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

/********
RENDERING
********/

MediaBrowser = function(cssSelector, json, isplaylist, playlistlabel){
    "use strict";
    var s = MediaBrowser.static
    $(cssSelector).off('click');
    $(cssSelector).on('click', '.listdir', s.listdirclick);
    $(cssSelector).on('click', '.compactlistdir', s.listdirclick);
    $(cssSelector).on('click', '.mp3file', s.addThisTrackToPlaylist);
    $(cssSelector).on('click', '.addAllToPlaylist', function() {
        if(isplaylist){
            var pl = playlistManager.newPlaylist([], playlistlabel);
        } else {
            var pl = playlistManager.getEditingPlaylist();
        }
        MediaBrowser.static._addAllToPlaylist($(this), pl.id);
        if(isplaylist){
            pl.setSaved(true);
        }
        $(this).blur();
        return false;
    });
    $(cssSelector).html(s._renderList(json));
    playlistManager.setTrackDestinationLabel();
    s.albumArtLoader(cssSelector);
}
MediaBrowser.static = {
    _renderList: function (l){
        "use strict";
        var self = this;
        var html = "";
        var foundMp3 = false;
        $.each(l, function(i, e) {
            if("file" == e.type){
                foundMp3 = true;
                return false;
            }
        });
        var addAll = '';
        if(foundMp3){
            addAll =    '<li><a class="addAllToPlaylist" href="javascript:;">'+
                            '<span class="add-track-destination">load playlist</span>'+
                        '</a></li>';
        }
        $.each(l, function(i, e) {
            switch(e.type){
                case 'dir': 
                    html += MediaBrowser.static._renderDirectory(e);
                    break;
                case 'file':
                    html += MediaBrowser.static._renderFile(e);
                    break;
                case 'compact':
                    html += MediaBrowser.static._renderCompactDirectory(e);
                    break;
                default:
                    window.console.log('cannot render unknown type '+e.type);
            }
        });
        if(html==""){
            html += MediaBrowser.static._renderMessage('No playable media files here.');
        }
        return '<ul>'+addAll+html+'</ul>';
    },
    
    _renderMessage : function(msg){
        return [
            '<li class="fileinlist">',
                '<div style="text-align: center">'+msg+'</div>',
            '</li>'
        ].join('');
    },
    _renderFile : function(json){
        return Mustache.render([
            '<li class="fileinlist">',
                '<a title="{{label}}" href="javascript:;" class="mp3file" path="{{fileurl}}">',
                    '<span class="fullpathlabel">',
                        '{{fullpath}}',
                    '</span>',
                    '{{label}}',
                '</a>',
            '</li>'
        ].join(''),
        {
            fileurl : json.urlpath,
            fullpath: json.path,
            label: json.label,
        });
    },
    _renderDirectory : function(json){
        return Mustache.render([
            '<li>',
                '<a dir="{{dirpath}}" href="javascript:;" class="listdir">',
                    '{{^isrootdir}}',
                            '{{{coverartfetcher}}}',
                    '{{/isrootdir}}',
                    '<div class="listdir-name-wrap">',
                        '<span class="listdir-name">{{dirpath}}</span>',
                    '</div>',
                '</a>',
            '</li>',
        ].join(''),
        {
            isrootdir: json.path && !json.path.indexOf('/')>0,
            dirpath: json.path,
            coverartfetcher: function(){
                return MediaBrowser.static._renderCoverArtFetcher(json.path)
            },
        });
    },
    _renderCompactDirectory : function(json){
        return Mustache.render([
        '<li>',
           '<a dir="{{filepath}}" filter="{{filter}}" href="javascript:;" class="compactlistdir">',
                '{{filterUPPER}}',
            '</a>',
        '</li>',
        ].join(''),
        {
            filepath: json.urlpath,
            filter: json.label,
            filterUPPER: json.label.toUpperCase(),
        });
    },
    
    _renderCoverArtFetcher : function(path){
        "use strict";
        var searchterms = encodeURIComponent(JSON.stringify({'directory' : path}))
        return ['<div class="albumart-display unloaded" search-data="'+searchterms+'">',
        '<img src="res/img/folder.png" width="80" height="80" />', // relative path so cherrymusic can run in subdir (#344)
        '</div>'].join('');
    },
        
    addThisTrackToPlaylist : function(){
        "use strict"
        playlistManager.addSong( $(this).attr("path"), $(this).attr("title") );
        $(this).blur();
        return false;
    },
    
    _addAllToPlaylist : function($source, plid){
        "use strict";
        $source.parent().siblings('li').children('.mp3file').each(function(){
            playlistManager.addSong( $(this).attr("path"), $(this).attr("title"), plid );
        });
    },
    
    listdirclick : function(mode){
        "use strict";
        if($(this).siblings('ul').length>0){
            if($(this).siblings('ul').is(":visible")){
                $(this).siblings('ul').slideUp('fast');
            } else {
                $(this).siblings('ul').slideDown('fast');
            }
        } else {
            var directory = $(this).attr("dir");
            var compactlisting = $(this).is("[filter]");
            if(compactlisting){
                var data = {
                    'action' : 'compactlistdir',
                    'value' : JSON.stringify({ 
                                'directory' : directory,
                                'filter' : $(this).attr("filter")
                              })
                };
            } else {
                var data = {
                    'action' : 'listdir',
                    'value' : JSON.stringify({
                                'directory' : directory 
                              })
                };
            }
            var currdir = this;
            var success = function(data){
                var json = jQuery.parseJSON(data);
                $(currdir).parent().append(MediaBrowser.static._renderList(json));
                playlistManager.setTrackDestinationLabel();
                $(currdir).siblings("ul").hide().slideDown('fast');
                MediaBrowser.static.albumArtLoader();
            };
            busy($(currdir).parent()).hide().fadeIn();
            api(data,
                success,
                errorFunc('unable to list compact directory'),
                function(){busy($(currdir).parent()).fadeOut('fast')});
        }
    },    
    albumArtLoader: function(cssSelector){
        "use strict";
        var winpos = $(window).height()+$(window).scrollTop();
        $('.albumart-display.unloaded').each(
            function(idx){
                if($(this).position().top < winpos){
                   $(this).find('img').attr('src', 'api/fetchalbumart/'+$(this).attr('search-data'));
                   $(this).removeClass('unloaded');
                }
            }
        );
    }
}
