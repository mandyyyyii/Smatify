var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;
var xhr = new XMLHttpRequest();

var fs = require('fs');

var express = require('express'); // Express web server framework
var request = require('request'); // "Request" library
var cors = require('cors');
var querystring = require('querystring');
var cookieParser = require('cookie-parser');

var client_id = 'cc5b2ffbefcf4fe2ad332912ff286885'; // Your client id
var client_secret = '7a17a50d9af7478cad0f08e8fae70736'; // Your secret
var redirect_uri = 'http://localhost:8888/callback'; // Your redirect uri

var SpotifyWebApi = require('spotify-web-api-node');

// credentials are optional
var spotifyApi = new SpotifyWebApi();

/**
 * Generates a random string containing numbers and letters
 * @param  {number} length The length of the string
 * @return {string} The generated string
 */
var generateRandomString = function (length) {
    var text = '';
    var possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

    for (var i = 0; i < length; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
};

var stateKey = 'spotify_auth_state';

var app = express();

app.use(express.static(__dirname + '/public'))
    .use(cors())
    .use(cookieParser());

app.get('/login', function (req, res) {

    var state = generateRandomString(16);
    res.cookie(stateKey, state);

    // your application requests authorization
    var scope = 'user-library-modify user-library-read user-read-private user-read-email playlist-modify-public playlist-read-collaborative playlist-read-private playlist-modify-private user-top-read user-read-playback-position user-read-recently-played';
    res.redirect('https://accounts.spotify.com/authorize?' +
        querystring.stringify({
            response_type: 'code',
            client_id: client_id,
            scope: scope,
            redirect_uri: redirect_uri,
            state: state
        }));
});

app.get('/callback', function (req, res) {

    // your application requests refresh and access tokens
    // after checking the state parameter

    var code = req.query.code || null;
    var state = req.query.state || null;
    var storedState = req.cookies ? req.cookies[stateKey] : null;

    if (state === null || state !== storedState) {
        res.redirect('/#' +
            querystring.stringify({
                error: 'state_mismatch'
            }));
    } else {
        res.clearCookie(stateKey);
        var authOptions = {
            url: 'https://accounts.spotify.com/api/token',
            form: {
                code: code,
                redirect_uri: redirect_uri,
                grant_type: 'authorization_code'
            },
            headers: {
                'Authorization': 'Basic ' + (new Buffer(client_id + ':' + client_secret).toString('base64'))
            },
            json: true
        };

        request.post(authOptions, function (error, response, body) {
            if (!error && response.statusCode === 200) {

                var access_token = body.access_token,
                    refresh_token = body.refresh_token;

                spotifyApi.setAccessToken(access_token);

                //GETTING USER DATA
                var options = {
                    url: 'https://api.spotify.com/v1/me',
                    headers: { 'Authorization': 'Bearer ' + access_token },
                    json: true
                };

                // use the access token to access the Spotify Web API
                request.get(options, function (error, response, body) {
                    console.log(body);
                    try {
                        fs.writeFileSync("user_info.json", JSON.stringify(body));
                    } catch (err) {
                        console.error(err);
                    }
                });


                //GETTING PLAYLISTS
                spotifyApi.getUserPlaylists().then(
                    function (data) {
                        console.log('Playlists:', data.body);
                        try {
                            fs.writeFileSync("playlists.json", JSON.stringify(data.body));
                        } catch (err) {
                            console.error(err);
                        }
                    },
                    function (err) {
                        console.error(err);
                    }
                );

                //GETTING TOP 50 SONGS
                spotifyApi.getMyTopTracks({limit:50}).then(
                    function (data) {
                        console.log('Top tracks:', data.body);
                        try {
                            fs.writeFileSync("top_tracks.json", JSON.stringify(data.body, null, 2));
                        } catch (err) {
                            console.error(err);
                        }
                    },
                    function (err) {
                        console.error(err);
                    }
                );
                
                console.log(typeof playlists);

                // we can also pass the token to the browser to make requests from there
                res.redirect('/#' +
                    querystring.stringify({
                        access_token: access_token,
                        refresh_token: refresh_token
                    }));
            } else {
                res.redirect('/#' +
                    querystring.stringify({
                        error: 'invalid_token'
                    }));
            }
        });
    }
});

app.get('/refresh_token', function (req, res) {

    // requesting access token from refresh token
    var refresh_token = req.query.refresh_token;
    var authOptions = {
        url: 'https://accounts.spotify.com/api/token',
        headers: { 'Authorization': 'Basic ' + (new Buffer(client_id + ':' + client_secret).toString('base64')) },
        form: {
            grant_type: 'refresh_token',
            refresh_token: refresh_token
        },
        json: true
    };

    request.post(authOptions, function (error, response, body) {
        if (!error && response.statusCode === 200) {
            var access_token = body.access_token;
            res.send({
                'access_token': access_token
            });
        }
    });
});

console.log('Listening on 8888');
app.listen(8888);
