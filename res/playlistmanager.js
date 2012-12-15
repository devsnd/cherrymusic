
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
        this.jplayerplaylist.add(track);
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
	});
    this.initJPlayer();
}

PlaylistManager.prototype = {
    initJPlayer : function(){
        "use strict";
        var self = this;
        if (typeof self.jPlayerInstance === 'undefined'){
            // Instance jPlayer
            self.jPlayerInstance = $(self.cssSelectorjPlayer).jPlayer({
                swfPath: "res/js",
                solution: "flash, html",
                preload: 'metadata',
                supplied: availablejPlayerFormats.join(),
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
                self.getPlayingPlaylist().jplayerplaylist.previous();
                $(this).blur();
                return false;
            });

            $(this.cssSelector.next).click(function() {
                self.getPlayingPlaylist().jplayerplaylist.next();
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
    checkFlashBlock : function(){
        $('#jquery_jplayer_1 object').css('z-index', '10000');
        $('#jquery_jplayer_1 object').css('position', 'absolute');
        $('#jquery_jplayer_1 div').css('z-index', '10000');
        $('#jquery_jplayer_1 div').css('position', 'absolute');
        $('#jquery_jplayer_1 div').css('background-color', '#fff');
        this.flashSize('100%','80px');
        //detect firefox flashblock:
        if(typeof $('#jquery_jplayer_1 div').attr('dataattribute') !== 'undefined'){
            errorFunc('Flashblock is enabled. Please click on the flash symbol on top of the player to activate flash.')();
        } else {
            window.clearInterval(this.flashBlockCheckIntervalId);
            removeError('Flashblock is enabled. Please click on the flash symbol on top of the player to activate flash.');
        }

    },
    flashSize : function(w, h){
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
        var cmds =$(this.cssSelectorPlaylistCommands);
        cmds.empty();
        var epl = this.getEditingPlaylist();
        if(typeof epl !== 'undefined'){
            if(epl.reason_open == 'queue'){
                cmds.append('<a class="button floatright" onclick="playlistManager.removePlayedFromPlaylist()" >remove played tracks</a>');
                cmds.append('<a class="button floatright" onclick="playlistManager.clearQueue()">clear queue</a>');
                cmds.append('<a class="button floatleft" onclick="playlistManager.newPlaylistFromQueue()">save as playlist</a>');
            } else {
                if(!epl.saved){
                    cmds.append('<a class="button" onclick="showPlaylistSaveDialog('+epl.id+')">save</a>');
                }
                /*cmds.append('<span class="floatleft">owner '+pl.owner+'</span>');
                if(!pl.public){
                    cmds.append('<span class="floatleft">status: <a class="button" title="make public">private</a></span>');
                } else {
                    cmds.append('<span class="floatleft">status: <a class="button" title="make private">public</a></span>');
                }*/
            }

            var remaintracks = epl.getRemainingTracks();
            var remaintimesec = epl.getPlayTimeSec(remaintracks);
            var completetimesec = epl.getPlayTimeSec(epl.jplayerplaylist.playlist);
            if(epl.id === this.getPlayingPlaylist().id){
                remaintimesec -= $(this.cssSelectorjPlayer).data("jPlayer").status.currentTime;
            }
            if(typeof remaintimesec !== 'undefined' && typeof completetimesec !== 'undefined' ){
                var proc = remaintimesec/completetimesec;
                var remaindisplay = '<div>'+epl.jplayerplaylist._formatTime(remaintimesec)+' remaining</div>';
            } else {
                var proc = remaintracks.length/epl.jplayerplaylist.playlist.length;
                var remaindisplay = '<div>'+remaintracks.length+' remaining tracks</div>';
            }
            var progressbar = '<div style="background-color: #ffffff;"><div style="width: '+parseInt(100-proc*100)+'%; height: 3px;" class="active"></div>';
            cmds.append('<div class="playlist-progress">'+remaindisplay+progressbar+'</div>');
        }
    },
    refreshTabs : function(){
        "use strict";
        window.console.log('refreshTabs');
        var self = this;
        var pltabs = '';
        for(var i=0; i<this.managedPlaylists.length; i++){
            var pl = this.managedPlaylists[i];
            pltabs += '<li id="'+this.tabid2htmlid(pl.id)+'" class="bigtab';
            if(pl.id == this.editingPlaylist){
                pltabs += ' active ';
            }
            var isplaying = '';
            if(pl.id == this.playingPlaylist){
                isplaying += '&#9654;';
            }
            pltabs += '"><span><a href="#" onclick="playlistManager.showPlaylist('+pl.id+')">'+isplaying+' '+pl.name+'</a>';
            if(pl.closable){
                pltabs += '<a href="#" onclick="playlistManager.closePlaylist('+pl.id+')">&times;</a>';
            }
            pltabs += '<span></li>';
        }
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
        $('#playlistBrowser').hide();
        var self = this;
        var showpl = $('#'+this.plid2htmlid(playlistid));
        this.hideAll();
        $('#addPlaylist ul li').removeClass('active');
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
        var pl = this.newPlaylist(this.managedPlaylists[0].jplayerplaylist.playlist);
        showPlaylistSaveDialog(pl.id);
        $(this).blur();
        return false;
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
        $('.plsmgr-editingplaylist-name').html(plname);
    },
    setPlayingPlaylist : function (plid){
        this.playingPlaylist = plid;
        this.refreshTabs();
    },
    addSong : function(path,title){
        "use strict";
        var self = this;
        var ext = getFileTypeByExt(path);
        var track = {
            title: title,
            wasPlayed : 0,
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

        this.getEditingPlaylist().addTrack(track);
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
            $('.cm-songtitle').html(jPlaylist.playlist[jPlaylist.current].title);
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
            if(cano.playlist.length){
                canonicalPlaylists.push(cano);
            }
        }
        var newToRememberPlaylist = JSON.stringify(canonicalPlaylists)
        if(this.lastRememberedPlaylist !== newToRememberPlaylist){
            // save playlist in session
            var data = {'action':'rememberplaylist',
                        'value': newToRememberPlaylist}
            var error = errorFunc('cannot rememebering playlist: failed to connect to server.');
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

                /*
                var pl = newPlaylist();
                pl._refresh(true);
                pl.active = true;
                self.refresh();
                //window.setInterval("rememberPlaylistPeriodically()",REMEMBER_PLAYLIST_INTERVAL );
                * */
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
        playlist = playlist || [];
        var newpl = this._createPlaylist(playlist,true,true,'me','ownwill', name);
        this.showPlaylist(newpl.id);
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
