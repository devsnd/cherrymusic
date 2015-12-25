app.factory('BrowseService', function(LegacyAPIService, $q){
    return {
        listDirectory: function(path){
            if(typeof path === 'undefined'){
                path = '';
            }
            return LegacyAPIService.post(
                'api/listdir', {'directory': path}
            );
        },
        search: function(searchterms){
            return LegacyAPIService.post(
                'api/search', {'searchstring': searchterms}
            );
        },
        fetchPlaylists: function(sortby, filterby){
            return LegacyAPIService.post(
                'api/showplaylists',
                {
                    'sortby': sortby,
                    'filterby': filterby,
                }
            );
        }
    }
})