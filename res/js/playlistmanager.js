
/* PLAYLIST CREATION AND MANAGEMENT */


var ManagedPlaylist = function(playlistManager, playlist, options){
    this.playlistManager = playlistManager;
    this.id = options.id;
    this.name = options.name;
    this.closable = options.closable;
    this.public = options.public;
    this.owner = options.owner;
    this.saved = options.saved;
    //can be 'recommendation', 'ownwill', 'queue'
    this.reason_open = options.reason_open;

    this.jplayerplaylist;
    this._init(playlist, playlistManager)
}
ManagedPlaylist.prototype = {
    _init : function(playlist, playlistManager){
        var self = this;
        this.playlistSelector = self._createNewPlaylistContainer();
        //check if playlist is sane:
        for(var i=0; i<playlist.length; i++){
            if(typeof playlist[0].path === 'undefined'){
                window.console.error('track has no path set!');
            }
            if(typeof playlist[0].label === 'undefined'){
                window.console.error('track has no label set!');
            }
        }
        self.jplayerplaylist = new jPlayerPlaylist(
            {
                jPlayer: this.playlistManager.cssSelectorjPlayer,
                cssSelectorAncestor: this.playlistManager.cssSelectorJPlayerControls
            },
            playlist,
            {   playlistOptions: {
                    'enableRemoveControls': true,
                    'playlistSelector': this.playlistSelector,
                    'playlistController' : this,
                    'loopOnPrevious': true
                },
                hooks: {
                    "setMedia": playlistManager.transcodeURL
                },
                loop: self.playlistManager.loop
            }
        );
        self.jplayerplaylist._init();
        // The following is a workaround to avoid jplayer to try to update the "shuffle" control
        // This is needed because we are currently not using the "shuffle" option of jplayer
        self.jplayerplaylist._updateControls = function() {
            playlistManager.refreshCommands();
        }
        $(self.playlistSelector+">ul.playlist-container-list").sortable({
            axis: "y",
            delay: 150,
            helper : 'clone',
            update: function(e,ui){
                self.jplayerplaylist.scan();
            }
        });
        $(self.playlistSelector+">ul.playlist-container-list").disableSelection();

        //event handler for clicked tracks in jplayer playlist
        $(this.playlistSelector).bind('requestPlay', function(event,playlistSelector) {
            self.playlistManager.setPlayingPlaylist(self.playlistManager.htmlid2plid(playlistSelector));
        });
        //event handler for clicked "x" for tracks in jplayer playlist
        $(this.playlistSelector).bind('removedItem', function(event,playlistSelector) {
            self.setSaved(false);
        });
        //event handler when items are sorted usin drag n drop
        $(this.playlistSelector).bind('sortedItems', function(event,playlistSelector) {
            self.setSaved(false);
        });
        //event handler when items are sorted usin drag n drop
        $(this.playlistSelector).bind('addedItem', function(event,playlistSelector) {
            self.setSaved(false);
        });
    },
    setSaved : function(issaved){
        this.saved = issaved;
        this.playlistManager.refreshCommands();
        this.playlistManager.refreshTabs();
    },
    wasSaved : function(){
        return this.saved;
    },
    _createNewPlaylistContainer : function(){
        var playlistContainerParent = this.playlistManager.cssSelectorPlaylistContainerParent;
        var id = this.playlistManager.plid2htmlid(this.id);
        $(playlistContainerParent).append(
            '<div class="playlist-container jp-playlist" id="'+id+'">'+
            '<ul class="playlist-container-list"><li></li></ul>'+
            '<div class="jp-playlist-playtime-sum"></div></div>'
        );
        return '#'+id;
    },
    getCanonicalPlaylist : function(){
        var canonical = [];
        for(var i=0; i<this.jplayerplaylist.playlist.length; i++){
            var elem = this.jplayerplaylist.playlist[i];
            var track = {
                title : elem.title,
                duration : elem.duration,
                url: elem.url,
                meta: elem.meta,
            }
            canonical.push(track);
        }
        return {
            'playlist' : canonical,
            'name' : this.name,
            'closable' : this.closable,
            'public' : this.public,
            'owner' : this.owner,
            'saved' : this.saved,
            'reason_open' : this.reason_open,
        };
    },
    getPlayTimeSec : function(playlist){
        var durationsec = 0;
        var tracks_with_duration = 0;
        for(var i=0; i<playlist.length; i++){
            if(typeof playlist[i].duration !== 'undefined'){
                durationsec += playlist[i].duration;
                tracks_with_duration++;
            }
        }
        if(tracks_with_duration == 0){
            // just show the number of track remaining
            return;
        } else {
            // estimate the length of the playlist
            return (durationsec / tracks_with_duration) * playlist.length;
        }
        
    },
    getRemainingTracks : function(){
        if(playlistManager.shuffled){
            var n = this._getMostPlayedTrack();
            var remainingTracks = this.jplayerplaylist.playlist.filter(function(elem,idx,arr){
                return elem.wasPlayed < n;
            });
            remainingTracks.push(this.jplayerplaylist.playlist[this.jplayerplaylist.current]);
            return remainingTracks
        } else {
            return this.jplayerplaylist.playlist.slice(this.jplayerplaylist.current);
        }
    },
    _getMostPlayedTrack : function(){
        var wasplayermost = 0;
        for(var i=0; i<this.jplayerplaylist.playlist.length; i++){
            if(this.jplayerplaylist.playlist[i].wasPlayed > wasplayermost){
                wasplayermost = this.jplayerplaylist.playlist[i].wasPlayed;
            }
        }
        return wasplayermost;
    },
    makeThisPlayingPlaylist : function(){
        this.playlistManager.setPlayingPlaylist(this.id);
    },
    addTrack : function(track, animate) {
        if(typeof animate === 'undefined'){
            animate = true;
        }
        this.jplayerplaylist.add(track, false, animate);
        this.scrollToTrack(this.jplayerplaylist.playlist.length-1);
    },
    scrollToTrack: function(number){
        var htmlid = '#'+playlistManager.plid2htmlid(this.id);
        var yoffset = $($(htmlid + ' > ul > li')[number]).position().top;
        var current_scroll = $('.playlist-container-parent').scrollTop();
        $('.playlist-container-parent').scrollTop(current_scroll + yoffset);
    },
    scrollToCurrentTrack: function(){
        this.scrollToTrack(this.jplayerplaylist.current);
    },
    sort_by: function(sort_by){
        this.jplayerplaylist.playlist.sort(
            function(a, b){
                var value_a = '';
                var value_b = '';
                if(typeof a.meta !== 'undefined'){
                    value_a = a.meta[sort_by];
                }
                if(typeof b.meta !== 'undefined'){
                    value_b = b.meta[sort_by];
                }
                // sort numerically if both values start with numbers
                if(!!value_a.match(/^\d+/) && !!value_b.match(/^\d+/)){
                    return parseInt(value_a) - parseInt(value_b);
                }
                // otherwise sort alphabetically
                if(value_a > value_b){
                    return 1;
                } else if(value_a < value_b){
                    return -1;
                } else {
                    return 0;
                }
            }
        );
        this.jplayerplaylist._refresh(true);
    }
}

var NewplaylistProxy = function(playlistManager){
    options = {};
    //override options
    options.id = 0;
    options.name = "new playlist";
    options.closable = false;
    options.public = true;
    options.owner = 'me';
    options.saved = true;
    options.reason_open = 'newplaylist_proxy';

    //create original object
    var actual = new ManagedPlaylist(playlistManager, [], options);

    //override methods
    actual.makeThisPlayingPlaylist = function(){
        var newpl = this.playlistManager.newPlaylist();
        newpl.makeThisPlayingPlaylist();
    };
    actual.addTrack = function(track) {
        var newpl = this.playlistManager.newPlaylist();
        this.playlistManager.setEditingPlaylist(newpl.id);
        newpl.jplayerplaylist.add(track);
    };
    return actual;
}

PlaylistManager = function(){
    "use strict";
    var self = this;
    this.cssSelectorPlaylistContainerParent = '.playlist-container-parent';
    this.cssSelectorPlaylistChooser = '#playlistChooser';
    this.cssSelectorPlaylistCommands = '#playlistCommands';
    this.cssSelectorJPlayerControls = '#jp_ancestor';
    this.cssSelectorjPlayer = "#jquery_jplayer_1";
    this.cssSelectorAlbumArt = "#albumart";
    this.newplaylistProxy = new NewplaylistProxy(this);
    this.managedPlaylists = [] //hold instances of ManagedPlaylist
    this.playingPlaylist = 0;
    this.editingPlaylist = 0;
    this.shuffled = false;
    this.cssSelector = {}
    this.lastRememberedPlaylist = '';
    this.nrOfCreatedPlaylists = 0;
    this.flashBlockCheckIntervalId;

    this.cssSelector.next = this.cssSelectorJPlayerControls + " .jp-next";
    this.cssSelector.previous = this.cssSelectorJPlayerControls + " .jp-previous";
    this.cssSelector.shuffle = this.cssSelectorJPlayerControls + " .jp-shuffle";
    this.cssSelector.shuffleOff = this.cssSelectorJPlayerControls + " .jp-shuffle-off";


    $(this.cssSelectorjPlayer).bind($.jPlayer.event.ready, function(event) {
        self.restorePlaylists();
        window.setInterval('playlistManager.displayCurrentSong()',1000);
        //used to update remaining playlist time:
        // should be triggered by jplayer time update event in the future.
        window.setInterval('playlistManager.refreshCommands()',1000);
        self.flashSize('0px','0px',-10000);
        //update formats that can be played:
        availablejPlayerFormats = []
        var jplayer = self.jPlayerInstance.data('jPlayer');
        if(jplayer.html.canPlay.oga || jplayer.flash.canPlay.oga){
            availablejPlayerFormats.push('opus');
            availablejPlayerFormats.push('ogg')
        }
        if(jplayer.html.canPlay.mp3 || jplayer.flash.canPlay.mp3){
            availablejPlayerFormats.push('mp3')
        }
        if(availablejPlayerFormats.length == 0){
            alert('Your browser does not support audio playback.');
        }
	});
    $(this.cssSelectorjPlayer).bind($.jPlayer.event.setmedia, function(event) {
        var playlist = self.getPlayingPlaylist().jplayerplaylist;
        var track = playlist.playlist[playlist.current];
        if (track) {
            self.setAlbumArtDisplay(track);
        }
    });
    this.initJPlayer();
}

PlaylistManager.prototype = {
    initJPlayer : function(){
        "use strict";

        //hack to use flash AND HTML solution in every case
        //https://github.com/happyworm/jPlayer/issues/136#issuecomment-12941923
        availablejPlayerFormats.push("m4v");

        var usedSolution = "html, flash";
        if(detectBrowser() == 'midori'){
            //WORKAROUND: the midori falsely reports mp3 support
            usedSolution = "flash, html";
        }
        var self = this;
        if (typeof self.jPlayerInstance === 'undefined'){
            // Instance jPlayer
            self.jPlayerInstance = $(self.cssSelectorjPlayer).jPlayer({
                swfPath: "res/js/ext",
                solution: usedSolution,
                preload: 'metadata',
                supplied: "mp3, oga, m4v",
                wmode: "window",
                cssSelectorAncestor: self.cssSelectorJPlayerControls,
                errorAlerts: false,
                repeat: self._getRepeatHandler()
            });
            this.cssSelector.next = this.cssSelectorJPlayerControls + " .jp-next";
            this.cssSelector.previous = this.cssSelectorJPlayerControls + " .jp-previous";
            this.cssSelector.shuffle = this.cssSelectorJPlayerControls + " .jp-shuffle";
            this.cssSelector.shuffleOff = this.cssSelectorJPlayerControls + " .jp-shuffle-off";

            /* JPLAYER EVENT BINDINGS */
            $(this.cssSelectorjPlayer).bind($.jPlayer.event.ended, function(event) {
                self.cmd_next();
            });

            /* WORKAROUND FOR BUG #343 (playback stops sometimes in google chrome) */
            $(this.cssSelectorjPlayer).bind($.jPlayer.event.error, function(event) {
                var now = new Date().getTime();
                 // there must be at least 5 seconds between errors, so we don't retry 1000 times.
                var min_error_gap_sec = 5;
                if(typeof self.jPlayerInstance.data("jPlayer").status.media.last_error === 'undefined'){
                    self.jPlayerInstance.data("jPlayer").status.media.last_error = 0;
                }
                var error_gap = now - self.jPlayerInstance.data("jPlayer").status.media.last_error;
                if(error_gap > min_error_gap_sec){
                    self.jPlayerInstance.data("jPlayer").status.media.last_error = now;
                    window.console.log("Playback failed! trying to resume from the point it failed.");
                    // get current time where playback failed and resume from there
                    var current_playtime = self.jPlayerInstance.data("jPlayer").status.currentTime;
                    playlistManager.jPlayerInstance.data("jPlayer").play(current_playtime);
                } else {
                    window.console.log("Playback failed too often! Trying next track.");
                    self.cmd_next();
                }
            });
            /* WORKAROUND END */

            /* JPLAYER CONTROLS BINDINGS */
            $(this.cssSelector.previous).click(function() {
                self.cmd_previous();
                $(this).blur();
                return false;
            });

            $(this.cssSelector.next).click(function() {
                self.cmd_next();
                $(this).blur();
                return false;
            });

            $(this.cssSelector.shuffle).click(function() {
                self.shuffleToggle();
                self.refreshShuffle();
                $(this).blur();
                return false;
            });
            $(this.cssSelector.shuffleOff).click(function() {
                self.shuffleToggle();
                self.refreshShuffle();
                $(this).blur();
                return false;
            });

            /* Set initial UI State */
            self.refreshShuffle();
            this.flashBlockCheckIntervalId = window.setInterval("playlistManager.checkFlashBlock()", 200);
        }
    },
    cmd_play : function(){
        $(this.cssSelectorjPlayer).jPlayer("play");
    },
    cmd_pause : function(){
        if($(this.cssSelectorjPlayer).data().jPlayer.status.paused){
            $(this.cssSelectorjPlayer).jPlayer("play");
        } else {
            $(this.cssSelectorjPlayer).jPlayer("pause");
        }
    },
    cmd_stop : function(){
        $(this.cssSelectorjPlayer).jPlayer("stop");
    },
    cmd_previous : function(){
        this.getPlayingPlaylist().jplayerplaylist.previous();
    },
    cmd_next : function(){
        if(this.shuffled){
            this.getPlayingPlaylist().jplayerplaylist.playRandomTrack();
            return false;
        } else {
            var currentPL = this.getPlayingPlaylist();
            currentPL.jplayerplaylist.next();
            if(currentPL.id == this.getEditingPlaylist().id){
                currentPL.scrollToCurrentTrack();
            }
            return false;
        }
    },
    checkFlashBlock : function(){
        flashBlocked = false;

        if(detectBrowser() == 'opera'){
            try {
                window.document.getElementById('jp_flash_0').SetVariable("flashblock", "flashblock");
            } catch(err) {
                flashBlocked = true;
            }
        } else {
            //works for firefox (and chrome?)
            flashBlocked = $('#jquery_jplayer_1 > div').length > 0;
        }

        if(flashBlocked){
            $('#jquery_jplayer_1 div').css('background-color', '#fff');
            this.flashSize('100%','80px','10000');
            errorFunc('Flashblock is enabled. Please click on the flash symbol on top of the player to activate flash.')();
        } else {
            window.clearInterval(this.flashBlockCheckIntervalId);
            window.setTimeout("playlistManager.flashSize('0px','0px',-10000);",1000);
            playlistManager.flashSize('0px','0px',-10000);
        }

    },
    flashSize : function(w, h, zidx){
        $('#jquery_jplayer_1 object').css('z-index', zidx);
        $('#jquery_jplayer_1 object').css('position', 'absolute');
        $('#jquery_jplayer_1 div').css('z-index', zidx);
        $('#jquery_jplayer_1 div').css('position', 'absolute');
        $('#jquery_jplayer_1 object').css('width', w);
        $('#jquery_jplayer_1 object').css('height', h);
        $('#jquery_jplayer_1 div').css('width', w);
        $('#jquery_jplayer_1 div').css('height', h);
    },
    shuffleToggle : function(){
      this.shuffled = !this.shuffled;
      this.refreshShuffle();
    },
    refresh : function(){
        var self = this;
        self.refreshTabs();
        self.refreshCommands();
        self.refreshPlaylists();
        self.refreshShuffle();
    },
    refreshShuffle : function(){
        if(this.shuffled){
            $(this.cssSelector.shuffle).hide();
            $(this.cssSelector.shuffleOff).show();
        } else {
            $(this.cssSelector.shuffle).show();
            $(this.cssSelector.shuffleOff).hide();
        }
    },
    refreshCommands : function(){
        var epl = this.getEditingPlaylist();
        if(typeof epl !== 'undefined'){
            show_ui_conditionally(
                ['.playlist-command-buttons',
                 '#playlist-command-button-group'],
                {
                    'queue': epl.reason_open == 'queue',
                    'playlist': epl.reason_open != 'queue',
                    'not-saved': epl.saved == false,
                    'user-may-download': userOptions.media.may_download,
                }
            );

            $('.save-current-playlist-button').off().on("click",function(){
                var epl = playlistManager.getEditingPlaylist();
                savePlaylist(epl.id, false,false,true);
                $(this).blur();
                return false;
            });

            $('.save-as-new-playlist-button').off().on("click",function(){
                var epl = playlistManager.getEditingPlaylist();
                $('#playlisttitle').val(epl.name+' copy');
                if(epl.public){
                    $("#playlistpublic").attr("checked", true);
                } else {
                    $("#playlistpublic").removeAttr("checked");
                }
            });

            var remaintracks = epl.getRemainingTracks();
            var completetimesec = epl.getPlayTimeSec(epl.jplayerplaylist.playlist);
            var remaintimesec = epl.getPlayTimeSec(remaintracks);
            var playingPlaylist = this.getPlayingPlaylist();
            var remainingStr = '';
            var proc = 0;

            // check if we are in shuffle mode, in this case just show the
            // complete playtime
            if (playlistManager.shuffled) {
                if (typeof completetimesec !== 'undefined' ) {
                    remainingStr = epl.jplayerplaylist._formatTime(completetimesec) + ' total'
                    proc = 1;
                }
            } else {
                if(playingPlaylist && epl.id === playingPlaylist.id){
                    remaintimesec -= $(this.cssSelectorjPlayer).data("jPlayer").status.currentTime;
                }
                remaintimesec = remaintimesec < 0 ? 0 : remaintimesec;

                var littleTimeLeft = false;

                if(typeof remaintimesec !== 'undefined' && typeof completetimesec !== 'undefined' ){
                    //if there is enough time info, show remaining time
                    if(completetimesec != 0){
                        proc = remaintimesec/completetimesec;
                    } else {
                        proc = 1;
                    }
                    littleTimeLeft = remaintimesec < 300;
                    remainingStr = (
                        epl.jplayerplaylist._formatTime(remaintimesec) +
                        ' / ' +
                        epl.jplayerplaylist._formatTime(completetimesec) +
                        ' remaining'
                    );
                } else {
                    //show remaining tracks
                    proc = remaintracks.length/epl.jplayerplaylist.playlist.length;
                    littleTimeLeft = remaintracks.length < 3;
                    remainingStr = (
                        remaintracks.length +
                        ' / ' +
                        epl.jplayerplaylist.playlist.length +
                        ' remaining tracks'
                    );
                }
                if(littleTimeLeft){
                    $('.remaining-tracks-or-time').removeClass('label-default');
                    $('.remaining-tracks-or-time').addClass('label-danger');
                    $('.playlist-progress-bar .progress-bar').addClass('progress-bar-danger');
                    $('.playlist-progress-bar .progress-bar').removeClass('progress-bar-default');
                } else {
                    $('.remaining-tracks-or-time').addClass('label-default');
                    $('.remaining-tracks-or-time').removeClass('label-danger');
                    $('.playlist-progress-bar .progress-bar').addClass('progress-bar-default');
                    $('.playlist-progress-bar .progress-bar').removeClass('progress-bar-danger');
                }
            }

            $('.remaining-tracks-or-time').html(remainingStr);
            $('.playlist-progress-bar .progress-bar').css('width',parseInt(100-proc*100)+'%');

        }
    },
    refreshTabs : function(){
        "use strict";
        window.console.log('refreshTabs');
        var self = this;
        var pltabs = '';
        for(var i=0; i<this.managedPlaylists.length; i++){
            var pl = this.managedPlaylists[i];

            var isactive = ''
            if(pl.id == this.editingPlaylist){
                isactive = ' class="active" ';
            } else {
                isactive = ' class="playlist-tab-inactive" ';
            }
            pltabs += '<li '+isactive+' id="'+this.tabid2htmlid(pl.id)+'">';

            var isplaying = '';
            if(pl.id == this.playingPlaylist){
                isplaying += '&#9654;';
            }

            var isunsaved = '';
            if(!pl.saved && pl.reason_open !== 'queue'){
                isunsaved += ' <em>(unsaved)</em>';
            }

            // fix for CVE-2015-8310
            var escaped_playlist_name = $("<div>").text(pl.name).html();
            pltabs += '<a href="#" onclick="playlistManager.showPlaylist('+pl.id+')">'+isplaying+' '+escaped_playlist_name + isunsaved;
            if(pl.closable){
                pltabs += '<span class="playlist-tab-closer pointer" href="#" onclick="playlistManager.closePlaylist('+pl.id+')">&times;</span>';
            }
            pltabs += '</a></li>';
        }
        pltabs += '<li class="playlist-tab-inactive playlist-tab-new"><a href="#" onclick="playlistManager.newPlaylist()"><b>+</b></a></li>';
        $(self.cssSelectorPlaylistChooser+' ul').empty()
        $(self.cssSelectorPlaylistChooser+' ul').append(pltabs);
    },
    tabid2htmlid : function(id){
        return this.plid2htmlid(id)+'-tab';
    },
    plid2htmlid : function(id){
        return 'pl-'+id;
    },
    htmlid2plid : function(htmlid){
        return parseInt(htmlid.slice(4,htmlid.length))
    },
    refreshPlaylists : function(){
        window.console.log('refreshPlaylists');
        var self = this;
        var validHTMLIds = [];
        for(var i=0; i<this.managedPlaylists.length; i++){
            validHTMLIds.push(this.plid2htmlid(this.managedPlaylists[i].id));
        }
        window.console.log(validHTMLIds);
        $.each($('#playlistContainerParent>div'), function(i,v){
            window.console.log($(this).attr('id'));
            if($.inArray($(this).attr('id'), validHTMLIds)<0){
                $(this).remove();
                window.console.log('removing invalid playlist from ui');
            }
        });

        this.showPlaylist(this.getEditingPlaylist().id);
    },
    showPlaylist : function(playlistid){
        $('#playlistCommands').show();
        $('#playlistContainerParent').show();
        $('#playlistBrowser').hide();
        var self = this;
        var plhtmlid = '#'+this.plid2htmlid(playlistid);
        var showpl = $(plhtmlid);
        this.hideAll();
        $('#playlistChooser ul li:last').removeClass('active');
        if(showpl.length<1){
            window.console.warn("tried showing playlist with htmlid "+plhtmlid+" which doesn't exist!");
            this.setEditingPlaylist(this.managedPlaylists[0].id);
            showpl = $('#'+this.plid2htmlid(this.getEditingPlaylist().id));
        } else {
            this.setEditingPlaylist(playlistid);
        }
        this.setTrackDestinationLabel();
        showpl.show();
        this.refreshTabs();
        this.refreshCommands();
    },
    setTrackDestinationLabel : function(){
        $('#searchresults .add-track-destination').text('add all to '+this.getEditingPlaylist().name);
    },
    hideAll : function(){
        $(this.cssSelectorPlaylistContainerParent+'>div').hide();
        $(this.cssSelectorPlaylistChooser+' ul li').removeClass('active');
        this.setEditingPlaylist(0);
    },
    getPlaylistById : function(plid){
        if (plid === 0) {
            return this.newplaylistProxy;
        }
        for(var i=0; i<this.managedPlaylists.length; i++){
            if(this.managedPlaylists[i].id == plid){
                return this.managedPlaylists[i];
            }
        }
    },
    getEditingPlaylist : function(){
        var pl = this.getPlaylistById(this.editingPlaylist);
        if(typeof pl !== 'undefined'){
            return pl;
        }
    },
    getPlayingPlaylist : function (){
        for(var i=0; i<this.managedPlaylists.length; i++){
            if(this.managedPlaylists[i].id == this.playingPlaylist){
                return this.managedPlaylists[i];
            }
        }
        return this.managedPlaylists[0];
    },
    newPlaylistFromQueue : function(){
        return this.newPlaylist(this.managedPlaylists[0].jplayerplaylist.playlist);
    },
    newPlaylistFromEditing : function(){
        return this.newPlaylist(this.getEditingPlaylist().jplayerplaylist.playlist);
    },

    closePlaylist : function(plid){
        for(var i=0; i<this.managedPlaylists.length; i++){
            if(this.managedPlaylists[i].id == plid){
                window.console.log('closing PL '+plid)
                this.managedPlaylists.splice(i,1);
                $('#'+this.plid2htmlid(plid)).remove()
                var otherId = this.managedPlaylists[i<this.managedPlaylists.length?i:0].id;
                window.console.log('showing '+otherId+' and using it as editing PL')
                this.showPlaylist(otherId)
                return false;
            }
        }
        this.refresh();
        $(this).blur();
        return false;
    },
    clearQueue : function(){
      this.managedPlaylists[0].jplayerplaylist.remove();
      this.refreshCommands();
      $(this).blur();
      return false;
    },
    setEditingPlaylist : function (editingplid){
        var plist = this.getPlaylistById(editingplid);
        var plname = '';
        if (typeof plist !== 'undefined') {
            this.editingPlaylist = editingplid;
            plname = plist.name;
        } else {
            window.console.error('Tried setting editing playlist to unknown id '+editingplid);
            this.editingPlaylist = 0;
            plname = 'unknown playlist'
        }
        $('.plsmgr-editingplaylist-name').text(plname);
    },
    setPlayingPlaylist : function (plid){
        this.playingPlaylist = plid;
        this.refreshTabs();
    },
    transcodeURL: function(track){
        "use strict";
        var self = this;
        var path = track.url;
        var title = track.title;
        var duration = track.duration;
        var ext = getFileTypeByExt(path);
        var track = {
            title: title,
            wasPlayed : 0,
            duration: duration,
        }
        var forced_bitrate = userOptions.media.force_transcode_to_bitrate;
        var formats = [];
        if(!(forced_bitrate) && availablejPlayerFormats.indexOf(ext) !== -1){
            //add natively supported path
            track[ext2jPlayerFormat(ext)] = SERVER_CONFIG.serve_path + path;
            formats.push(ext);
            window.console.log('added native format '+ext);
        } else if(!transcodingEnabled){
            //not natively supported (or bitrate limited) but no transcoding
            var msg = forced_bitrate ? "bitrate limit requested" : ("browser doesn't support filetype "+ext);
            msg += ' and transcoding is disabled. Transcoding can be enabled in the server configuration.';
            window.console.log(msg);
            return;
        } else {
            //try transcoding
            window.console.log('Trying available transcoders.');
            if(availableDecoders.indexOf(ext) === -1){
                window.console.log('missing decoder for filetype '+ext+'. track '+path+' can not be transcoded.')
                return;
            } else {
                for(var i=0; i<availablejPlayerFormats.length; i++){
                    if(availableEncoders.indexOf(availablejPlayerFormats[i]) !== -1){
                        formats.push(availablejPlayerFormats[i]);
                        var transurl = SERVER_CONFIG.transcode_path + availablejPlayerFormats[i] + '/' + path;
                        transurl += '?bitrate=' + forced_bitrate;
                        track[ext2jPlayerFormat(availablejPlayerFormats[i])] = transurl;
                        window.console.log('added live transcoding '+ext+' --> '+availablejPlayerFormats[i]+' @ '+transurl);
                    }
                }
            }
            if(formats.length == 0){
                window.console.log('no suitable encoder available! Try installing vorbis-tools or lame!');
                return;
            }
        }
        return track;
    },
    setAlbumArtDisplay : function(track) {
        if(userOptions.ui.display_album_art){
            // strip filename from url
            var directory = track.url;
            if (directory == '') // root directory
                directory = '/';
            var api_param = JSON.stringify({directory: directory});
            var imgurl = 'api/fetchalbumart?data=' + api_param;
            $(this.cssSelectorAlbumArt).attr('src', imgurl);
        }
    },
    addSong : function(path, title, plid, animate){
        "use strict";
        var self = this;
        if(typeof animate === 'undefined'){
            animate = true;
        }
        var track = {
            title: title,
            url: path,
            wasPlayed : 0,
        }
        var playlist;
        if (plid) {
            playlist = this.getPlaylistById(plid);
        }
        if (typeof playlist == 'undefined') {
            playlist = this.getEditingPlaylist();
        }
        playlist.addTrack(track, animate);

        //directly play/select first added track
        if(!jPlayerIsPlaying() && playlist.jplayerplaylist.playlist.length == 1){
            if(userOptions.misc.autoplay_on_add){
                playlist.makeThisPlayingPlaylist();
                playlist.jplayerplaylist.play(0);
            } else {
                playlist.jplayerplaylist.select(0);
            }
        }
        var success = function(data){
            var metainfo = $.parseJSON(data);
            var any_info_received = false;
            // save all the meta-data in the track
            track.meta = metainfo;
            if (metainfo.length) {
                track.duration = metainfo.length;
                any_info_received = true;
            }
            // only show id tags if at least artist and title are known
            if (metainfo.title.length > 0 && metainfo.artist.length > 0) {
                track.title = metainfo.artist+' - '+metainfo.title;
                if(metainfo.track.length > 0){
                    track.title = metainfo.track + ' ' + track.title;
                    if(metainfo.track.length < 2){
                        track.title = '0' + track.title;
                    }
                }
                any_info_received = true;
            }
            if(any_info_received){
                //only rerender playlist if it would visually change
                self.getEditingPlaylist().jplayerplaylist._refresh(true);
            }
        }
        // WORKAROUND: delay the meta-data fetching, so that a request
        // for the actual audio data comes through frist
         window.setTimeout(
            function(){
                api('getsonginfo', {'path': decodeURIComponent(path)}, success, errorFunc('error getting song metainfo'), true);
            },
            1000
        );
    },
    clearPlaylist : function(){
        "use strict";
        this.getEditingPlaylist().remove();
        if(this.getEditingPlaylist() == this.getPlayingPlaylist()){
            $(this.cssSelectorjPlayer).jPlayer("clearMedia");
        }
        return false;
    },
    displayCurrentSong : function (){
        var pl = this.getPlayingPlaylist();
        if(typeof pl === 'undefined'){
            return;
        }
        var jPlaylist = pl.jplayerplaylist;
        var songtitle = '';
        var tabtitle = 'CherryMusic';
        if(typeof this.jPlayerInstance !== 'undefined'){
            var currentTitle = this.jPlayerInstance.data().jPlayer.status.media.title;
            if(typeof currentTitle !== 'undefined'){
                songtitle = currentTitle;
                tabtitle = currentTitle+' | CherryMusic';
            }
        }
        $('.cm-songtitle').html(songtitle);
        $('title').text(tabtitle);
    },
    rememberPlaylist : function(){
        "use strict";
        var self = this;
        var canonicalPlaylists = []
        for(var i=0; i<this.managedPlaylists.length; i++){
            var cano = this.managedPlaylists[i].getCanonicalPlaylist();
            if(cano.playlist.length || cano.reason_open == 'queue'){
                canonicalPlaylists.push(cano);
            }
        }
        var newToRememberPlaylist = JSON.stringify(canonicalPlaylists)
        if(this.lastRememberedPlaylist !== newToRememberPlaylist){
            // save playlist in session
            var error = errorFunc('cannot remember playlist: failed to connect to server.');
            var success = function(){
                self.lastRememberedPlaylist = newToRememberPlaylist;
            }
            api('rememberplaylist', {'playlist': canonicalPlaylists}, success, error, true);
        }
    },
    restorePlaylists : function(){
        var self = this;
        "use strict";
        /*restore playlist from session*/
        var success = function(data){
            var playlistsToRestore = data;
            if(playlistsToRestore !== null && playlistsToRestore.length>0){
                window.console.log('restoring playlist from last session');
                for(var i=0; i<playlistsToRestore.length; i++){
                    var pl = playlistsToRestore[i];
                    var newpl = self._createPlaylist(pl.playlist,pl.closable,pl.public,pl.owner,pl.reason_open,pl.name,pl.saved);
                }
                self.setPlayingPlaylist(self.getPlayingPlaylist().id);
                self.showPlaylist();
            } else {
                var pl = self._createPlaylist([],false,false,'self','queue','Queue',true);
                self.playingPlaylist = pl.id;
                self.setEditingPlaylist(pl.id);
                self.showPlaylist(pl.id);
            }
            self.refresh();
            window.console.log('remembering playlists periodically');
            window.setInterval("playlistManager.rememberPlaylist()",REMEMBER_PLAYLIST_INTERVAL );
        };
        api('restoreplaylist', success, errorFunc('error restoring playlist'));
    },
    _createPlaylist : function(playlist, closable, public, owner, reason, name, saved){
        var a = new Date();
        var timemillis = a.getTime();
        if(typeof name === 'undefined'){
            this.nrOfCreatedPlaylists++;
            name = 'playlist '+this.nrOfCreatedPlaylists;
        }
        if(typeof saved === 'undefined'){
            saved = false;
        }
        var newpl = new ManagedPlaylist(
            this,
            playlist,
            {
                'id' : parseInt(timemillis),
                'name' : name,
                'closable' : closable,
                'public' : public,
                'owner' : owner,
                'reason_open' : reason,
                'saved' : saved,
            }
        );
        this.managedPlaylists.push(newpl);
        this.refresh();
        return newpl;
    },
    newPlaylist : function(playlist, name){
        var newpl = this.newPlaylistNoShow(playlist, name);
        this.showPlaylist(newpl.id);
        return newpl;
    },
    newPlaylistNoShow : function(playlist, name){
        playlist = playlist || [];
        var newpl = this._createPlaylist(playlist,true,false,'me','ownwill', name, true);
        return newpl;
    },
    removePlayedFromPlaylist : function (){
        var mediaPlaylist = this.getEditingPlaylist().jplayerplaylist;
        for(var i=0; i<mediaPlaylist.playlist.length; i++){
            var wasPlayed = mediaPlaylist.playlist[i].wasPlayed>0;
            var isCurrentTrack = i == mediaPlaylist.current;
            var isBeforeCurrent = i < mediaPlaylist.current;
            var clearCurrent = !jPlayerIsPlaying();
            if(wasPlayed && (!isCurrentTrack || clearCurrent)){
                mediaPlaylist.playlist.splice(i,1);
                i--;
                if(isBeforeCurrent){
                    mediaPlaylist.current--;
                }
            }
        }
        mediaPlaylist._refresh(true);
    },
    _getRepeatHandler : function() {
        var playlistManager = this;
        var _handleRepeat = function(event) {
            var repeatState = event.jPlayer.options.loop;
            playlistManager.loop = repeatState;
            $.each(playlistManager.managedPlaylists, function(i, playlist) {
                playlist.jplayerplaylist.loop = repeatState;
            });
        }
        return _handleRepeat;
    }
}
