/*
function displayMessageOfTheDay(){
    api('getmotd',
        function(resp){
            if(resp.type == 'update'){
                html = Mustache.render(
                    '<a href="http://fomori.org/cherrymusic/">'+
                        'CherryMusic {{version}} is available!'+
                        '<h2>download now →</h2>'+
                    '</a><hr>'+
                    '<h3>{{features_count}} new {{feature_title}}:</h3>'+
                    '<ul class="feature-list">'+
                    '   {{#features}}<li>{{.}}</li>{{/features}}'+
                    '</ul>'+
                    '<h3>{{fixes_count}} {{fixes_title}}:</h3>'+
                    '<ul class="feature-list">'+
                    '   {{#fixes}}<li>{{.}}</li>{{/fixes}}'+
                    '</ul><hr>'+
                    '<p>'+
                    '   And a lot of other stuff, see the'+
                    '   <a href="https://github.com/devsnd/cherrymusic/blob/{{version}}/CHANGES" target="_blank">'+
                    '   CHANGELOG</a>.'+
                    '</p>',
                    {
                        version: resp.data.version,
                        features: resp.data.features,
                        features_count: resp.data.features.length,
                        feature_title: resp.data.features.length > 1 ? 'features' : 'feature',
                        fixes: resp.data.fixes,
                        fixes_count: resp.data.fixes.length,
                        fixes_title: resp.data.fixes.length > 1 ? 'fixes' : 'fix',
                    });
                $('#motd').html(html);
            } else if(resp.type == 'wisdom'){
                $('#motd').html('useless wisdom<hr>'+resp.data);
            } else {
                window.console.error('unknown motd type '+resp.type);
            }
        },
        errorFunc('could not fetch message of the day')
    );
}
*/

app.factory('MOTDService', function(LegacyAPIService, $q){
    return {
        fetch: function(){
            return LegacyAPIService.post('api/getmotd');
        },
    }
});