
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
    this._init(playlist)
}
ManagedPlaylist.prototype = {
    _init : function(playlist){
        var self = this;
        this.playlistSelector = self._createNewPlaylistContainer();
        self.jplayerplaylist = new jPlayerPlaylist({
                jPlayer: this.playlistManager.cssSelectorjPlayer,
                cssSelectorAncestor: this.playlistManager.cssSelectorJPlayerControls
            },
            playlist,
            {   playlistOptions: {
                    'enableRemoveControls': true,
                    'playlistSelector': this.playlistSelector,
                    'playlistController' : this
                }
            }
        );
        self.jplayerplaylist._init();

        $(playlistSelector+" ul").sortable({
            update: function(e,ui){
                self.jplayerplaylist.scan();
            }
        });
        $(playlistSelector+" ul").disableSelection();

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
            '<div class="playlist-container jp-playlist" id="'+id+'"><ul><li></li></ul><div class="jp-playlist-playtime-sum"></div></div>'
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
            }
            if(typeof elem.mp3 !== 'undefined'){
                track.mp3 = elem.mp3
            }
            if(typeof elem.oga !== 'undefined'){
                track.oga = elem.oga
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
        for(var i=0; i<playlist.length; i++){
            if(typeof playlist[i].duration !== 'undefined'){
                durationsec += playlist[i].duration;
            } else {
                return;
            }
        }
        return durationsec;
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
    addTrack : function(track) {
        this.jplayerplaylist.add(track,false);
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
    this.cssSelectorPlaylistContainerParent = '#playlistContainerParent';
    this.cssSelectorPlaylistChooser = '#playlistChooser';
    this.cssSelectorPlaylistCommands = '#playlistCommands';
    this.cssSelectorJPlayerControls = '#jp_ancestor';
    this.cssSelectorjPlayer = "#jquery_jplayer_1";
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
            var usedjPlayerFormats = [];
            for(var i=0; i<availablejPlayerFormats.length; i++){
                usedjPlayerFormats.push(ext2jPlayerFormat(availablejPlayerFormats[i]));
            }
            // Instance jPlayer
            self.jPlayerInstance = $(self.cssSelectorjPlayer).jPlayer({
                swfPath: "res/js",
                solution: usedSolution,
                preload: 'metadata',
                supplied: "mp3,oga,m4v",
                wmode: "window",
                cssSelectorAncestor: self.cssSelectorJPlayerControls,
                errorAlerts: false,
            });
            this.cssSelector.next = this.cssSelectorJPlayerControls + " .jp-next";
            this.cssSelector.previous = this.cssSelectorJPlayerControls + " .jp-previous";
            this.cssSelector.shuffle = this.cssSelectorJPlayerControls + " .jp-shuffle";
            this.cssSelector.shuffleOff = this.cssSelectorJPlayerControls + " .jp-shuffle-off";

            /* JPLAYER EVENT BINDINGS */
            $(this.cssSelectorjPlayer).bind($.jPlayer.event.ended, function(event) {
                if(self.shuffled){
                   self.getPlayingPlaylist().jplayerplaylist.playRandomTrack();
                   return false;
                } else {
                    self.getPlayingPlaylist().jplayerplaylist.next();
                    return false;
                }
            });

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
        this.getPlayingPlaylist().jplayerplaylist.next();
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
            //works for firefox and chrome    
            flashBlocked = typeof $('#jquery_jplayer_1 div').attr('dataattribute') !== 'undefined';
        }
        
        if(flashBlocked){ 
            $('#jquery_jplayer_1 div').css('background-color', '#fff');
            this.flashSize('100%','80px','10000');
            errorFunc('Flashblock is enabled. Please click on the flash symbol on top of the player to activate flash.')();
        } else {
            window.clearInterval(this.flashBlockCheckIntervalId);
            removeError('Flashblock is enabled. Please click on the flash symbol on top of the player to activate flash.');
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
            if(epl.reason_open == 'queue'){
                $('.new-playlist-from-queue').show();
                $('.clear-playlist').show();
                $('.remove-played-tracks').show();
                $('.save-current-playlist').hide();
            } else {
                $('.new-playlist-from-queue').hide();
                $('.clear-playlist').hide();
                $('.remove-played-tracks').hide();
                if(!epl.saved){
                    $('.save-current-playlist').off(); //remove old handlers
                    $('.save-current-playlist').on("click",function(){
                        savePlaylist(epl.id,false,false,true);
                        $(this).blur();
                        return false;
                    });
                    $('.save-current-playlist').show();
                } else {
                    $('.save-current-playlist').hide();
                }
            }
            
            var remaintracks = epl.getRemainingTracks();
            var completetimesec = epl.getPlayTimeSec(epl.jplayerplaylist.playlist);
            var remaintimesec = epl.getPlayTimeSec(remaintracks);
            var playingPlaylist = this.getPlayingPlaylist();
            if(playingPlaylist && epl.id === playingPlaylist.id){
                remaintimesec -= $(this.cssSelectorjPlayer).data("jPlayer").status.currentTime;
            }
            remaintimesec = remaintimesec < 0 ? 0 : remaintimesec;
            
            var littleTimeLeft = false;
            var remainingStr = '';
            var proc = 0;
            if(typeof remaintimesec !== 'undefined' && typeof completetimesec !== 'undefined' ){
                //if there is enough time info, show remaining time
                proc = remaintimesec/completetimesec;
                littleTimeLeft = remaintimesec < 300;
                remainingStr = epl.jplayerplaylist._formatTime(remaintimesec)+' remaining'
            } else {
                //show remaining tracks
                proc = remaintracks.length/epl.jplayerplaylist.playlist.length;
                littleTimeLeft = remaintracks.length < 3;
                remainingStr = remaintracks.length+' remaining tracks';
            }
            if(littleTimeLeft){
                $('.remaining-tracks-or-time').addClass('label-important');
                $('.playlist-progress-bar .bar').addClass('bar-danger');
            } else {
                $('.remaining-tracks-or-time').removeClass('label-important');
                $('.playlist-progress-bar .bar').removeClass('bar-danger');
            }
            $('.remaining-tracks-or-time').html(remainingStr);           
            $('.playlist-progress-bar .bar').css('width',parseInt(100-proc*100)+'%');
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
            
            
            pltabs += '<a href="#" onclick="playlistManager.showPlaylist('+pl.id+')">'+isplaying+' '+pl.name+ isunsaved;
            if(pl.closable){
                pltabs += '<span class="playlist-tab-closer pointer" href="#" onclick="playlistManager.closePlaylist('+pl.id+')">&times;</span>';
            }
            pltabs += '</a></li>';
        }
        pltabs += '<li><a href="#" onclick="playlistManager.showPlaylistBrowser()"><b>+</b></a></li>';
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
        $('#playlistBrowser').hide();
        var self = this;
        var showpl = $('#'+this.plid2htmlid(playlistid));
        this.hideAll();
        $('#playlistChooser ul li:last').removeClass('active');
        if(showpl.length<1){
            this.setEditingPlaylist(this.managedPlaylists[0].id);
            showpl = $('#'+this.plid2htmlid(this.getEditingPlaylist().id));
        } else {
            this.setEditingPlaylist(playlistid);
        }
        showpl.show();
        this.refreshTabs();
        this.refreshCommands();
    },
    showPlaylistBrowser: function(){
        playlistManager.hideAll();
        playlistManager.setEditingPlaylist(0);
        showPlaylists();
        $('#playlistChooser ul li:last').addClass('active');
        $('#playlistCommands').hide();
        $('#playlistBrowser').show();
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
    closePlaylist : function(plid){
        for(var i=0; i<this.managedPlaylists.length; i++){
            if(this.managedPlaylists[i].id == plid){
                this.managedPlaylists.splice(i,1);
                var otherId = this.managedPlaylists[i<this.managedPlaylists.length?i:0].id;
                this.setEditingPlaylist(otherId);
                this.playingPlaylist = otherId;
                break;
            }
        }
        this.refresh();
        $(this).blur();
        return false;
    },
    clearQueue : function(){
      this.managedPlaylists[0].jplayerplaylist.remove();
      $(this).blur();
      return false;
    },
    setEditingPlaylist : function (plid){
        var plist = this.getPlaylistById(plid);
        var plname = '';
        if (typeof plist !== 'undefined') {
            this.editingPlaylist = plid;
            plname = plist.name;
        } else {
            this.editingPlaylist = 0;
            plname = 'unknown playlist'
        }
        $('.plsmgr-editingplaylist-name').text(plname);
    },
    setPlayingPlaylist : function (plid){
        this.playingPlaylist = plid;
        this.refreshTabs();
    },
    addSong : function(path,title, plid){
        "use strict";
        var self = this;
        var ext = getFileTypeByExt(path);
        var track = {
            title: title,
            wasPlayed : 0,
        }
        var formats = [];
        if(availablejPlayerFormats.indexOf(ext) !== -1){
            //add natively supported path
            track[ext2jPlayerFormat(ext)] = path;
            formats.push(ext);
            window.console.log('added native format '+ext);
        } else if(!transcodingEnabled){
            //not natively supported and no transcoding
            window.console.log("browser doesn't support filetype "+ext+'and transcoding is disabled. Transcoding can be enabled in the server configuration.');
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
                        track[ext2jPlayerFormat(availablejPlayerFormats[i])] = getTranscodePath(path,availablejPlayerFormats[i]);
                        window.console.log('added live transcoding '+ext+' --> '+availablejPlayerFormats[i]);
                    }
                }
            }
            if(formats.length == 0){
                window.console.log('no suitable encoder available! Try installing vorbis-tools or lame!');
                return;
            }
        }


        var playlist;
        if (plid) {
            playlist = this.getPlaylistById(plid);
        }
        if (typeof playlist == 'undefined') {
            playlist = this.getEditingPlaylist();
        }

        playlist.addTrack(track);
        pulse('.tabNavigation li a.jplayer');
        var success = function(data){
            var metainfo = $.parseJSON(data)
            if (metainfo.length) {
                track.duration = metainfo.length;
            }
            self.getEditingPlaylist().jplayerplaylist._refresh(true);
        }
        api({action:'getsonginfo',
            value: path}, success, errorFunc('error getting song metainfo'), true);
    },
    clearPlaylist : function(){
        "use strict";
        getEditingPlaylist().remove();
        return false;
    },
    displayCurrentSong : function (){
        var pl = this.getPlayingPlaylist();
        if(typeof pl === 'undefined'){
            return;
        }
        var jPlaylist = pl.jplayerplaylist;
        if(jPlaylist.playlist && typeof jPlaylist.current !== 'undefined' && jPlaylist.playlist.length>0){
            $('.cm-songtitle').text(jPlaylist.playlist[jPlaylist.current].title);
            return
        }
        $('.cm-songtitle').html('');
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
            var data = {'action':'rememberplaylist',
                        'value': newToRememberPlaylist}
            var error = errorFunc('cannot remember playlist: failed to connect to server.');
            var success = function(){
                self.lastRememberedPlaylist = newToRememberPlaylist;
            }
            api(data, success, error, true);
        }
    },
    restorePlaylists : function(){
        var self = this;
        "use strict";
        /*restore playlist from session*/
        var success = function(data){
            var playlistsToRestore = $.parseJSON(data);
            window.console.log(playlistsToRestore);
            if(playlistsToRestore !== null && playlistsToRestore.length>0){
                window.console.log('should restore playlist now');
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
        api('restoreplaylist',success,errorFunc('error restoring playlist'));
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
            if(mediaPlaylist.playlist[i].wasPlayed>0){
                mediaPlaylist.playlist.splice(i,1);
                i--;
            }
        }
        mediaPlaylist._refresh(false);
    }
}
