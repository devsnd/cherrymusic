/*
 * Playlist Object for the jPlayer Plugin
 * http://www.jplayer.org
 *
 * Copyright (c) 2009 - 2011 Happyworm Ltd
 * Dual licensed under the MIT and GPL licenses.
 *  - http://www.opensource.org/licenses/mit-license.php
 *  - http://www.gnu.org/copyleft/gpl.html
 *
 * Author: Mark J Panaghiston
 * Version: 2.1.0 (jPlayer 2.1.0)
 * Date: 1st September 2011
 */

/* Code verified using http://www.jshint.com/ */
/*jshint asi:false, bitwise:false, boss:false, browser:true, curly:true, debug:false, eqeqeq:true, eqnull:false, evil:false, forin:false, immed:false, jquery:true, laxbreak:false, newcap:true, noarg:true, noempty:true, nonew:true, nomem:false, onevar:false, passfail:false, plusplus:false, regexp:false, undef:true, sub:false, strict:false, white:false */
/*global  jPlayerPlaylist: true, jQuery:false, alert:false */

(function($, undefined) {

	jPlayerPlaylist = function(cssSelector, playlist, options) {
		var self = this;

        this.active = false;
		this.current = 0;
		this.loop = false; // Flag used with the jPlayer repeat event
		this.shuffled = false;
		this.removing = false; // Flag is true during remove animation, disabling the remove() method until complete.

		this.cssSelector = $.extend({}, this._cssSelector, cssSelector); // Object: Containing the css selectors for jPlayer and its cssSelectorAncestor
		this.options = $.extend(true, {}, this._options, options); // Object: The jPlayer constructor options for this playlist and the playlist options

		this.playlist = []; // Array of Objects: The current playlist displayed (Un-shuffled or Shuffled)
		this.original = []; // Array of Objects: The original playlist

		this._initPlaylist(playlist); // Copies playlist to this.original. Then mirrors this.original to this.playlist. Creating two arrays, where the element pointers match. (Enables pointer comparison.)

		// Setup the css selectors for the extra interface items used by the playlist.
		this.cssSelector.title = this.cssSelector.cssSelectorAncestor + " .jp-title"; // Note that the text is written to the decendant li node.
		if(this.options.playlistOptions.playlistSelector) {
			this.cssSelector.playlist = this.options.playlistOptions.playlistSelector;
		} else {
			this.cssSelector.playlist = this.cssSelector.cssSelectorAncestor + " .jp-playlist";
		}
		this.cssSelector.next = this.cssSelector.cssSelectorAncestor + " .jp-next";
		this.cssSelector.previous = this.cssSelector.cssSelectorAncestor + " .jp-previous";
		this.cssSelector.shuffle = this.cssSelector.cssSelectorAncestor + " .jp-shuffle";
		this.cssSelector.shuffleOff = this.cssSelector.cssSelectorAncestor + " .jp-shuffle-off";

		// Override the cssSelectorAncestor given in options
		this.options.cssSelectorAncestor = this.cssSelector.cssSelectorAncestor;

		// Override the default repeat event handler
		this.options.repeat = function(event) {
			self.loop = event.jPlayer.options.loop;
		};

		// Create a ready event handler to initialize the playlist
        // is now handled by cherrymusic
		/*$(this.cssSelector.jPlayer).bind($.jPlayer.event.ready, function(event) {
			self._init();
		});*/

		// Create an ended event handler to move to the next item
		/*$(this.cssSelector.jPlayer).bind($.jPlayer.event.ended, function(event) {
            if(self.active){
                self.next();
            }
		});*/

		// Create a play event handler to pause other instances
		$(this.cssSelector.jPlayer).bind($.jPlayer.event.play, function(event) {
			$(this).jPlayer("pauseOthers");
		});

		// Create a resize event handler to show the title in full screen mode.
		$(this.cssSelector.jPlayer).bind($.jPlayer.event.resize, function(event) {
			if(event.jPlayer.options.fullScreen) {
				$(self.cssSelector.title).show();
			} else {
				$(self.cssSelector.title).hide();
			}
		});

		// Put the title in its initial display state
		if(!this.options.fullScreen) {
			$(this.cssSelector.title).hide();
		}

		// Remove the empty <li> from the page HTML. Allows page to be valid HTML, while not interfereing with display animations
		$(this.cssSelector.playlist + " ul.playlist-container-list").empty();

		// Create .live() handlers for the playlist items along with the free media and remove controls.
		this._createItemHandlers();

		
	};

	jPlayerPlaylist.prototype = {
		_cssSelector: { // static object, instanced in constructor
			jPlayer: "#jquery_jplayer_1",
			cssSelectorAncestor: "#jp_container_1"
		},
		_options: { // static object, instanced in constructor
			playlistOptions: {
				autoPlay: false,
				loopOnPrevious: false,
				shuffleOnLoop: true,
				enableRemoveControls: false,
				displayTime: 'slow',
				addTime: 'fast',
				removeTime: 'fast',
				shuffleTime: 'slow',
				itemClass: "jp-playlist-item",
				freeGroupClass: "jp-free-media",
				freeItemClass: "jp-playlist-item-free",
				removeItemClass: "jp-playlist-item-remove",
				actionItemClass: "jp-playlist-item-action",
				parentFolderItemClass: "jp-playlist-item-show-parent-folder",
				playlistSelector: false,
				playtimeClass: "jp-playlist-playtime",
			},
            hooks: {
                //can transform track before playing in jPlayer
                "setMedia" : function(track){return track}, 
            },
		},
		option: function(option, value) { // For changing playlist options only
			if(value === undefined) {
				return this.options.playlistOptions[option];
			}

			this.options.playlistOptions[option] = value;

			switch(option) {
				case "enableRemoveControls":
					this._updateControls();
					break;
				case "itemClass":
				case "freeGroupClass":
				case "freeItemClass":
				case "removeItemClass":
					this._refresh(true); // Instant
					this._createItemHandlers();
					break;
			}
			return this;
		},
		_init: function() {
			var self = this;
			this._refresh(function() {
				if(self.options.playlistOptions.autoPlay) {
					self.play(self.current);
				}
			});
		},
		_initPlaylist: function(playlist) {
            for(var i=0; i<playlist.length; i++){
                if(typeof playlist[i].wasPlayed === 'undefined'){
                    playlist[i].wasPlayed = 0;
                }
            }
			this.current = 0;
			this.shuffled = false;
			this.removing = false;
			this.original = $.extend(true, [], playlist); // Copy the Array of Objects
			this._originalPlaylist();
		},
		_originalPlaylist: function() {
			var self = this;
			this.playlist = [];
			// Make both arrays point to the same object elements. Gives us 2 different arrays, each pointing to the same actual object. ie., Not copies of the object.
			$.each(this.original, function(i,v) {
				self.playlist[i] = self.original[i];
			});
		},
		_refresh: function(instant) {
			/* instant: Can be undefined, true or a function.
			 *	undefined -> use animation timings
			 *	true -> no animation
			 *	function -> use animation timings and excute function at half way point.
			 */
			var self = this;

			if(instant && !$.isFunction(instant)) {
				$(this.cssSelector.playlist + " ul.playlist-container-list").empty();
				$.each(this.playlist, function(i,v) {
					$(self.cssSelector.playlist + " ul.playlist-container-list").append(self._createListItem(self.playlist[i]));
                    var litem = $(self.cssSelector.playlist + " > ul > li:last");
                    litem.attr('name', litem.index());
				});
				this._updateControls();
			} else {
				var displayTime = $(this.cssSelector.playlist + " ul.playlist-container-list").children().length ? this.options.playlistOptions.displayTime : 0;

				$(this.cssSelector.playlist + " ul.playlist-container-list").slideUp(displayTime, function() {
					var $this = $(this);
					$(this).empty();
					
					$.each(self.playlist, function(i,v) {
                        $this.append(self._createListItem(self.playlist[i]));
						var litem = $(self.cssSelector.playlist + " > ul.playlist-container-list > li:last");
                        litem.attr('name', litem.index());
					});
					self._updateControls();
					if($.isFunction(instant)) {
						instant();
					}
					if(self.playlist.length) {
						$(this).slideDown(self.options.playlistOptions.displayTime);
					} else {
						$(this).show();
					}
				});
			}
            this._updatePlaytime();
            this._highlight(this.current);
            this._createItemHandlers();
		},
        _updatePlaytime: function(){
            var self = this;
            var playtimeSum = 0;
		    $.each(this.playlist, function(i,v) {
			if(self.playlist[i].duration){
			    playtimeSum += self.playlist[i].duration;
			}
		    });
		    if(playtimeSum){
                $(self.cssSelector.playlist+"-playtime-sum").html("<div><span href='javascript:;'>"+self._formatTime(playtimeSum)+"</span></div>");
		    } else {
                $(self.cssSelector.playlist+"-playtime-sum").html("");
            }  
        },
		_formatTime: function(secs) {
			secs = Math.floor(secs);
            var mins = Math.floor(secs/60);
            var hours = Math.floor(mins/60);
            
			var s = secs%60;
			if(s<10){ s='0'+s; }
			var m = mins%60;
			if(m<10){ m='0'+m; }
            var h = hours>0 ? hours+':' : '';
			return h+m+':'+s;
		},
		_createListItem: function(media) {
			var self = this;

			// Wrap the <li> contents in a <div>
			var listItem = "<li><div>";

            // create track action menu
			listItem += '<div class="btn-group ' + this.options.playlistOptions.actionItemClass + '">'+
            '  <button type="button" class="btn-transparent btn-xs dropdown-toggle" data-toggle="dropdown">'+
            '    <span class="caret"></span>'+
            '  </button>'+
            '  <ul class="dropdown-menu" role="menu">'+
            '    <li><a class="'+this.options.playlistOptions.parentFolderItemClass+'" href="#">Show parent folder</a></li>'+
            '  </ul>'+
            '</div>';
            
			// Create Playtime
            if(media.duration){
                listItem += "<span href='javascript:;' class='" + this.options.playlistOptions.playtimeClass + "'>"+self._formatTime(media.duration)+"</span>";
            }
			// Create remove control
			listItem += "<a href='javascript:;' class='" + this.options.playlistOptions.removeItemClass + "'>&times;</a>";
            

			// Create links to free media
			if(media.free) {
				var first = true;
				listItem += "<span class='" + this.options.playlistOptions.freeGroupClass + "'>(";
				$.each(media, function(property,value) {
					if($.jPlayer.prototype.format[property]) { // Check property is a media format.
						if(first) {
							first = false;
						} else {
							listItem += " | ";
						}
						listItem += "<a class='" + self.options.playlistOptions.freeItemClass + "' href='" + value + "' tabindex='1'>" + property + "</a>";
					}
				});
				listItem += ")</span>";
			}

			// The title is given next in the HTML otherwise the float:right on the free media corrupts in IE6/7
			listItem += "<a href='javascript:;' class='" + this.options.playlistOptions.itemClass + "' tabindex='1'>" + media.title + (media.artist ? " <span class='jp-artist'>by " + media.artist + "</span>" : "") + "</a>";
			listItem += "</div></li>";

			return listItem;
		},
		_createItemHandlers: function() {
			var self = this;
			// Create .live() handlers for the playlist items
			$(this.cssSelector.playlist + " a." + this.options.playlistOptions.itemClass).off("click").on("click", function() {
                $(self.options.playlistOptions.playlistSelector).trigger('requestPlay', [self.options.playlistOptions.playlistSelector]);
				var index = $(this).parent().parent().index();
				//if(self.current !== index) {
					self.play(index);
				//} else {
				//	$(self.cssSelector.jPlayer).jPlayer("play");
				//}
				$(this).blur();
				return false;
			});

			// Create .live() handlers that disable free media links to force access via right click
			$(self.cssSelector.playlist + " a." + this.options.playlistOptions.freeItemClass).off("click").on("click", function(event) {
				$(this).parent().parent().find("." + self.options.playlistOptions.itemClass).click();
				$(this).blur();
				return false;
			});

			// Create .live() handlers for the remove controls
			$(self.cssSelector.playlist + " a." + this.options.playlistOptions.removeItemClass).off("click").on("click", function(event) {
                event.stopPropagation();
				var index = $(this).parent().parent().index();
				self.remove(index);
				$(this).blur();
				return false;
			});
            
            // create handlers for showing the parent folder of a file
            $(self.cssSelector.playlist + " a." + this.options.playlistOptions.parentFolderItemClass).off('click').on("click", function(event) {
                var index = $(this).parent().parent().parent().parent().parent().index();
                var folder = decodeURIComponent(self.playlist[index].url);
                lastFolderSeparator = folder.lastIndexOf('/');
                if(lastFolderSeparator == -1){
                    // if there is no "/" in the path it is the basedir
                    folder = '';
                } else {
                    folder = folder.slice(0, lastFolderSeparator);
                }
                loadBrowser(folder, folder);
            });
		},
		_updateControls: function() {
			if(this.options.playlistOptions.enableRemoveControls) {
				$(this.cssSelector.playlist + " ." + this.options.playlistOptions.removeItemClass).show();
			} else {
				$(this.cssSelector.playlist + " ." + this.options.playlistOptions.removeItemClass).hide();
			}
			if(this.shuffled) {
				$(this.cssSelector.shuffleOff).show();
				$(this.cssSelector.shuffle).hide();
			} else {
				$(this.cssSelector.shuffleOff).hide();
				$(this.cssSelector.shuffle).show();
			}
		},
		_highlight: function(index) {
			if(this.playlist.length && index !== undefined) {
				$(this.cssSelector.playlist + " .jp-playlist-current").removeClass("jp-playlist-current");
				$(this.cssSelector.playlist + ">ul>li:nth-child(" + (index + 1) + ")").addClass("jp-playlist-current").find(".jp-playlist-item").addClass("jp-playlist-current");
				$(this.cssSelector.title + " li").html(this.playlist[index].title + (this.playlist[index].artist ? " <span class='jp-artist'>by " + this.playlist[index].artist + "</span>" : ""));
			}
		},
		setPlaylist: function(playlist) {
			this._initPlaylist(playlist);
			this._init();
		},
		add: function(media, playNow, animate) {
            var self = this;
            if(typeof animate === 'undefined'){
                animate = true;
            }
            if(animate){
                $(this.cssSelector.playlist + " ul.playlist-container-list").append(this._createListItem(media)).find("li:last-child").hide().slideDown(this.options.playlistOptions.addTime);
            } else {
                $(this.cssSelector.playlist + " ul.playlist-container-list").append(this._createListItem(media));
            }
			this._updateControls();
            this._createItemHandlers();
			this.original.push(media);
			this.playlist.push(media); // Both array elements share the same object pointer. Comforms with _initPlaylist(p) system.

			if(playNow) {
				this.play(this.playlist.length - 1);
			} /*else {
				if(this.original.length === 1) {
					this.select(0);
				}
			}*/
            $(self.options.playlistOptions.playlistSelector).trigger('addedItem', [self.options.playlistOptions.playlistSelector]);
		},
		remove: function(index) {
			var self = this;
            $(self.options.playlistOptions.playlistSelector).trigger('removedItem', [self.options.playlistOptions.playlistSelector]);
			if(index === undefined) {
				this._initPlaylist([]);
				this._refresh(function() {
                    if(self.active){
                        $(self.cssSelector.jPlayer).jPlayer("clearMedia");
                    }
				});
				return true;
			} else {

				if(this.removing) {
					return false;
				} else {
					index = (index < 0) ? self.original.length + index : index; // Negative index relates to end of array.
					if(0 <= index && index < this.playlist.length) {
						this.removing = true;

						$(this.cssSelector.playlist + ">ul>li:nth-child(" + (index + 1) + ")").slideUp(this.options.playlistOptions.removeTime, function() {
							$(this).remove();

							if(self.shuffled) {
								var item = self.playlist[index];
								$.each(self.original, function(i,v) {
									if(self.original[i] === item) {
										self.original.splice(i, 1);
										return false; // Exit $.each
									}
								});
								self.playlist.splice(index, 1);
							} else {
								self.original.splice(index, 1);
								self.playlist.splice(index, 1);
							}

							if(self.original.length) {
								if(index === self.current) {
									self.current = (index < self.original.length) ? self.current : self.original.length - 1; // To cope when last element being selected when it was removed
									self.select(self.current);
								} else if(index < self.current) {
									self.current--;
								}
							} else {
								$(self.cssSelector.jPlayer).jPlayer("clearMedia");
								self.current = 0;
								self.shuffled = false;
								self._updateControls();
							}
                            self._updatePlaytime();
							self.removing = false;
                            //make sure all "name" attributes are correctly numbered
                            self._refresh(true);
						});
					}
					return true;
				}
			}
		},
		select: function(index) {
			index = (index < 0) ? this.original.length + index : index; // Negative index relates to end of array.
			if(0 <= index && index < this.playlist.length) {
				this.current = index;
				this._highlight(index);
                this.playlist[this.current].wasPlayed += 1;
                var self = this;
				$(this.cssSelector.jPlayer).jPlayer("setMedia", 
                    self.options.hooks["setMedia"](this.playlist[this.current])
                );
			} else {
				this.current = 0;
			}
		},
		play: function(index) {
			index = (index < 0) ? this.original.length + index : index; // Negative index relates to end of array.
			if(0 <= index && index < this.playlist.length) {
				if(this.playlist.length) {
					this.select(index);
					$(this.cssSelector.jPlayer).jPlayer("play");
				}
			} else if(index === undefined) {
				$(this.cssSelector.jPlayer).jPlayer("play");
			}
		},
		pause: function() {
			$(this.cssSelector.jPlayer).jPlayer("pause");
		},
		next: function() {
            if(this.shuffled){
                playRandomTrack();
            } else {
                var index = (this.current + 1 < this.playlist.length) ? this.current + 1 : 0;
                // The index will be zero if it just looped round
				if(this.loop || index > 0) {
					this.play(index);
				}
            }
		},
        playRandomTrack: function(){
            var weighted = [];
            for(var i=0; i<this.playlist.length; i++){
                if( typeof this.playlist[i].wasPlayed === 'undefined' ){
                    this.playlist.wasPlayed[i] = 0;
                }
                weighted.push([i,this.playlist[i].wasPlayed]);
            }
            weighted.sort(function(a,b){
                return a[1]-b[1]
            });
            //pick from top half of least played tracks
            var index = weighted[parseInt(Math.random()*this.playlist.length/2)][0];
            this.play(index);  
        },
		previous: function() {
            if(this.shuffled){
                playRandomTrack();
            } else {
                var index = (this.current - 1 >= 0) ? this.current - 1 : this.playlist.length - 1;
                if(this.loop && this.options.playlistOptions.loopOnPrevious || index < this.playlist.length - 1) {
                    this.play(index);
                }
            }
		},
		shuffle: function(shuffled, playNow) {
			this.shuffled = !this.shuffled;
            this._updateControls();
		},
        scan: function() {
            var self = this;
            var isAdjusted = false;

            var replace = [];
            $.each($(this.cssSelector.playlist + " > ul.playlist-container-list > li"), function(index, value) {
                replace[index] = self.original[$(value).attr('name')];
                if(!isAdjusted && self.current === parseInt($(value).attr('name'), 10)) {
                    self.current = index;
                    isAdjusted = true;
                }
                $(value).attr('name', index);
            });
            this.original = replace;
            this._originalPlaylist();
            $(self.options.playlistOptions.playlistSelector).trigger('sortedItems', [self.options.playlistOptions.playlistSelector]);
        }
	};
})(jQuery);
