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

/********
RENDERING
********/

MediaBrowser = function(cssSelector, json, title, enable_breadcrumbs, options){
    "use strict";
    this.listing_data_stack = [{'title': title, 'data': json, 'scroll': 0, 'listview': false}];
    this.cssSelector = cssSelector;
    $(this.cssSelector).css('left', 0);
    if(typeof enable_breadcrumbs === 'undefined'){
        enable_breadcrumbs = true;
    }
    this.options = typeof options === 'undefined'? {} : options;

    var self = this;

    var listdirclick = function(){

        "use strict";
        $(self.cssSelector+' .cm-media-list-category').animate({left: '-100%'}, {duration: 1000, queue: false});
        $(self.cssSelector).addClass('cm-media-list-busy');
        var last_scroll_pos = $(self.cssSelector).parent().parent().scrollTop();
        $(self.cssSelector).parent().parent().scrollTop(0);
        var next_mb_title = '';
        var directory = $(this).attr("dir");
        var compactlisting = $(this).is("[filter]");
        var action = 'listdir';
        var dirdata = {'directory' : directory};
        if(compactlisting){
            action = 'compactlistdir';
            dirdata['filterstr'] = $(this).attr("filter");
            next_mb_title = 'Filter: '+dirdata['filterstr'];
        } else {
            next_mb_title = $(this).text();
        }
        var currdir = this;
        var success = function(json){
            $(self.cssSelector).removeClass('cm-media-list-busy');
            var last_stack_top = self.listing_data_stack[self.listing_data_stack.length-1];
            last_stack_top.scroll = last_scroll_pos;
            self.listing_data_stack.push({'title': next_mb_title, 'data': json, 'scroll': 0, 'listview': last_stack_top.listview});
            self.render();
        };
        var error = function(){
            $(self.cssSelector).removeClass('cm-media-list-busy');
            errorFunc('unable to list compact directory');
        }
        api(action,
            dirdata,
            success,
            error);
        $(this).blur();
        return false;
    }

    var view_list_enable = function(){
        self.listing_data_stack[self.listing_data_stack.length-1].listview = true;
        self.render();
    }

    var view_cover_enable = function(){
        self.listing_data_stack[self.listing_data_stack.length-1].listview = false;
        self.render();
    }

    this.go_to_parent = function(levels){
        if(typeof levels === 'undefined'){
            levels = 1;
        }
        for(var i=0; i<levels; i++){
            self.listing_data_stack.pop();
        }
    }

    this.render = function(){
        var stack_top = self.listing_data_stack[self.listing_data_stack.length-1]['data'];
        var listview_enabled = self.listing_data_stack[self.listing_data_stack.length-1].listview;
        //split into categories:
        var folders = [];
        var files = [];
        var compact = [];
        var playlist = []
        for(var i=0; i < stack_top.length; i++){
            var e = stack_top[i];
            if("file" == e.type){
                files.push(e);
            } else if("dir" == e.type){
                folders.push(e);
            } else if("compact" == e.type){
                compact.push(e);
            } else if("playlist" == e.type){
                playlist.push(e);
            } else {
                window.console.error('unknown media browser item '+e.type);
            }
        }
        var filehtml = MediaBrowser.static._renderList(files, listview_enabled);
        var folderhtml = MediaBrowser.static._renderList(folders, listview_enabled);
        var compacthtml = MediaBrowser.static._renderList(compact, listview_enabled);
        var playlisthtml = MediaBrowser.static._renderList(playlist, listview_enabled);

        var html = '';
        if('' != folderhtml){
            html += '<div class="cm-media-list-category"><h3>Collections'+
            '<div class="input-group-btn btn-group-xs cm-media-list-view-change-buttons">'+
            '    <button type="button" class="mb-view-cover-enable btn btn-default">'+
            '        <span class="glyphicon glyphicon-th-large"></span>'+
            '    </button>'+
            '    <button type="button" class="mb-view-list-enable btn btn-default">'+
            '        <span class="glyphicon glyphicon-th-list"></span>'+
            '    </button>'+
            '</div>'+
            '</h3>'+
            '<ul class="cm-media-list">'+folderhtml+'</ul></div>';
        }
        if('' != filehtml){
            html += '<div class="cm-media-list-category"><h3>Tracks <a href="#" class="btn btn-default" '+
                    'onclick="MediaBrowser.static._addAllToPlaylist($(this).parent().siblings(\'ul\'))">'+
                    'add all tracks to current playlist</a>'+
                    '</h3><ul class="cm-media-list">'+filehtml+'</ul></div>';
        }
        if('' != compacthtml){
            html += '<div class="cm-media-list-category"><h3>Compact</h3>'+
                    '<ul class="cm-media-list">'+compacthtml+'</ul></div>';
        }
        if('' != playlisthtml || self.options.showPlaylistPanel){
            html += '<div class="cm-media-list-category"><h3>Playlists</h3>'+
                    '<div class="row">'+
                        '<div class="col-md-6">'+
                            '<div class="btn-group input-group-sm">'+
                                '<span class="input-group-addon">sort by</span>'+
                                '<div class="input-group-btn">'+
                                    '<button type="button" class="btn btn-default" onclick="showPlaylists(\'title\', $(\'.playlist-filter-input\').val())">'+
                                        '<span class="glyphicon glyphicon-sort-by-alphabet"></span> title'+
                                    '</button>'+
                                    '<button type="button" class="btn btn-default" onclick="showPlaylists(\'username\', $(\'.playlist-filter-input\').val())">'+
                                        '<span class="glyphicon glyphicon-user"></span> user'+
                                    '</button>'+
                                    '<button type="button" class="btn btn-default" onclick="showPlaylists(\'age\', $(\'.playlist-filter-input\').val())">'+
                                        '<span class="glyphicon glyphicon-time"></span> age'+
                                    '</button>'+
                                '</div>'+
                            '</div>'+
                        '</div>'+
                        '<div class="col-md-6">'+
                            '<div class="input-group input-group-sm">'+
                              '<input type="text" class="playlist-filter-input form-control" placeholder="title or trackname"'+
                              'onchange="showPlaylists(\'\', $(\'.playlist-filter-input\').val())">'+
                              '<span class="input-group-btn">'+
                                '<button type="submit" onclick="showPlaylists(\'\', $(\'.playlist-filter-input\').val())" class="btn btn-default">Search</button>'+
                              '</span>'+
                            '</div>'+
                        '</div>'+
                    '</div>'+
                    '<ul class="cm-media-list">'+playlisthtml+'</ul></div>';
        }
        if('' == html){
            html = '<div class="cm-media-list-category"><ul class="cm-media-list">'+MediaBrowser.static._renderMessage('No playable media files here.')+'</ul></div>';
        }

        if(enable_breadcrumbs){
            html = '<ol class="breadcrumb"></ol>' + html;
        }
        $(self.cssSelector).html(html);

        var create_jump_func = function(i){
            return function(){
                self.go_to_parent(self.listing_data_stack.length - 1 - i);
                self.render();
            };
        }
        if(self.listing_data_stack.length > 1){
            var node = $('<div class="cm-media-list-item cm-media-list-parent-item">'+
            '   <a class="cm-media-list-parent" href="javascript:;">'+
            '   <span class="glyphicon glyphicon-arrow-left"></span>'+
            '</a></div>');
            node.on('click', create_jump_func(self.listing_data_stack.length-2));
            $(this.cssSelector).prepend(node);
        }
        if(enable_breadcrumbs){
            for(var i=0; i < self.listing_data_stack.length; i++){
                var title = self.listing_data_stack[i]['title'];
                var li = '<li';
                if(i == self.listing_data_stack.length - 1){
                    li += ' class="active"';
                }
                li += '><a href="#">'+title+'</a></li>';
                var $li = $(li);
                $li.on('click', create_jump_func(i));
                $(this.cssSelector + ' .breadcrumb').append($li);
            }
        }
        $(self.cssSelector).parent().parent().scrollTop(self.listing_data_stack[self.listing_data_stack.length-1].scroll);

        playlistManager.setTrackDestinationLabel();
        MediaBrowser.static.albumArtLoader('#search-panel');
    }

    this.render();
    // remove all old click handlers
    $(cssSelector).off('click');
    // register current click handlers for all list items
    $(cssSelector).on('click', '.list-dir', listdirclick);
    $(cssSelector).on('click', '.compact-list-dir', listdirclick);
    $(cssSelector).on('click', '.musicfile', MediaBrowser.static.addThisTrackToPlaylist);
    $(cssSelector).on('click', '.cm-media-list-wrench', function(){
        var dirname = decodeURIComponent($(this).attr('data-dirname'));
        $('#changeAlbumArt').attr('data-dirname', $(this).attr('data-dirname'));
        $('#changeAlbumArt .foldername').text(dirname)
        $('#changeAlbumArt').modal('show');
    });
    // register list and cover view buttons
    $(cssSelector).on('click', '.mb-view-list-enable', view_list_enable);
    $(cssSelector).on('click', '.mb-view-cover-enable', view_cover_enable);

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
}

MediaBrowser.static = {
    _renderList: function (l, listview){
        "use strict";
        var self = this;
        var html = "";
        $.each(l, function(i, e) {
            switch(e.type){
                case 'dir':
                    html += MediaBrowser.static._renderDirectory(e, listview);
                    break;
                case 'file':
                    html += MediaBrowser.static._renderFile(e);
                    break;
                case 'compact':
                    html += MediaBrowser.static._renderCompactDirectory(e);
                    break;
                case 'playlist':
                    html += MediaBrowser.static._renderPlaylist(e);
                    break;
                default:
                    window.console.log('cannot render unknown type '+e.type);
            }
        });
        return html;
    },

    _renderMessage : function(msg){
        var template = templateLoader.cached('mediabrowser-message');
        return Mustache.render(template, {message: msg});
    },
    _renderFile : function(json){
        var template = templateLoader.cached('mediabrowser-file');
        var template_data = {
            fileurl : json.urlpath,
            fullpath: json.path,
            label: json.label,
        };
        return Mustache.render(template, template_data);
    },
    _renderDirectory : function(json, listview){
        var template = templateLoader.cached('mediabrowser-directory');
        var template_data = {
            isrootdir: json.path && !json.path.indexOf('/')>0,
            dirpath: json.path,
            label: json.label,
            listview: listview,
            maychangecoverart: !!isAdmin,
            coverarturl: encodeURIComponent(JSON.stringify({'directory' : json.path})),
            directoryname: encodeURIComponent(json.path),
            foldercount: json.foldercount,
            showfoldercount: json.foldercount > 0,
            filescount: json.filescount,
            showfilescount: json.filescount > 0,
            filescountestimate: json.filescountestimate,

        };
        return Mustache.render(template, template_data);
    },
    _renderPlaylist : function(e){
        var template = templateLoader.cached('mediabrowser-playlist');
        var template_data = {
            playlistid: e['plid'],
            isowner: e.owner,
            candelete: e.owner || isAdmin,
            playlistlabel:e['title'],
            encodedplaylistlabel:encodeURI(e['title']),
            username: e['username'],
            age: time2text(e['age']),
            username_color: userNameToColor(e.username),
            publicchecked: e['public'] ? 'checked="checked"' : '',
            publiclabelclass : e['public'] ? 'label-success' : 'label-default',
        };
        return Mustache.render(template, template_data);
    },
    _renderCompactDirectory : function(json){
        var template = templateLoader.cached('mediabrowser-compact');
        var template_data = {
            filepath: json.urlpath,
            filter: json.label,
            filterUPPER: json.label.toUpperCase(),
        };
        return Mustache.render(template, template_data);
    },

    addThisTrackToPlaylist : function(){
        "use strict"
        playlistManager.addSong( $(this).attr("path"), $(this).attr("title") );
        $(this).blur();
        return false;
    },

    _addAllToPlaylist : function($source, plid){
        "use strict";
        $source.find('li .musicfile').each(function(){
            playlistManager.addSong( $(this).attr("path"), $(this).attr("title"), plid );
        });
    },

    albumArtLoader: function(cssSelector){
        "use strict";
        var winheight = $(window).height();
        var scrolled_down = $(cssSelector).scrollTop();
        var preload_threshold = 50; //pixels
        $(cssSelector).find('.list-dir-albumart.unloaded').each(
            function(idx){
                var img_pos = $(this).position().top;
                var above_screen = img_pos < scrolled_down - preload_threshold;
                var below_screen = img_pos > winheight + scrolled_down + preload_threshold;
                if(!above_screen && !below_screen){
                    $(this).find('img').attr('src', 'api/fetchalbumart/?data='+$(this).attr('search-data'));
                    $(this).removeClass('unloaded');
                }
            }
        );
        var renderMetaData = function(selector, metainfo){
            console.log('renderMetaData');
            // only use tag info if at least artist and title are known
            if (metainfo.artist.length > 0 && metainfo.title.length > 0) {
                selector.find('.meta-info-artist').text(
                    metainfo.artist
                );
                selector.find('.meta-info-title').text(
                    metainfo.title
                );
                if(metainfo.track.length > 0){
                    if(metainfo.track.length < 2){
                        metainfo.track = '0' + metainfo.track;
                    }
                    selector.find('.meta-info-track').text(
                        metainfo.track
                    );
                }
                selector.parent().find('.simplelabel').hide();
            }
            // show length anyway, if it was detemined.
            if(metainfo.length){
                selector.find('.meta-info-length').text(
                    '('+jPlayerPlaylist.prototype._formatTime(metainfo.length) + ')'
                );
            }
        }

        var fetch_meta_data = function(elem){
            var jqelem = $(elem);
            console.log('fetch_meta_data');
            var track_pos = jqelem.parent().position().top;
            var above_screen = track_pos < scrolled_down - preload_threshold;
            var below_screen = track_pos > winheight + scrolled_down + preload_threshold;
            if(!above_screen && !below_screen){
                var self = jqelem;
                var path_url_enc = jqelem.attr('path');
                var success = function(data){
                    $(self).show();
                    var metainfo = $.parseJSON(data);
                    renderMetaData($(self), metainfo);
                }
                var complete = function(){
                    jqelem.removeClass('unloaded');
                    load_unloaded_meta_data(cssSelector);
                }
                api(
                    'getsonginfo',
                    {'path': decodeURIComponent(path_url_enc)},
                    success,
                    errorFunc('error getting song metainfo'),
                    complete
                );
            }
        }

        var load_unloaded_meta_data = function(cssSelector){
            console.log('load_unloaded_meta_data');
            var unloaded_metadata = $(cssSelector).find('.meta-info.unloaded');
            if(unloaded_metadata.length > 0){
                fetch_meta_data(unloaded_metadata[0]);
            }
        }
        load_unloaded_meta_data(cssSelector);

    },
}

