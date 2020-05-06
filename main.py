import pymongo
import pprint
import pymysql
import json

from flask import Flask, flash, render_template, request, redirect, g, session
from pymongo import MongoClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from spotify_requests import spotify

# credit for spotify api: https://github.com/mari-linhares/spotify-flask

try:
    import configparser
except:
    from six.moves import configparser




app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:cs411project@localhost/smartify'
SQL_db = SQLAlchemy(app)

class Artist(SQL_db.Model):

    __tablename__ = 'top_artists'

    artist_id = SQL_db.Column(SQL_db.String(225), nullable=False, primary_key=True)
    artist_name = SQL_db.Column(SQL_db.String(225), nullable=False)
    popularity = SQL_db.Column(SQL_db.Integer, nullable=False)
    rating = SQL_db.Column(SQL_db.Integer, nullable=False)


class Song(SQL_db.Model):

    __tablename__ = 'top_songs'

    song_id = SQL_db.Column(SQL_db.String(225), nullable=False, primary_key=True)
    song_name = SQL_db.Column(SQL_db.String(225), nullable=False)
    artist_name = SQL_db.Column(SQL_db.String(225), nullable=False)
    popularity = SQL_db.Column(SQL_db.Integer, nullable=False)
    rating = SQL_db.Column(SQL_db.Integer, nullable=False)

# SQL connection
engine = create_engine('mysql+pymysql://root:cs411project@localhost/smartify')

# mongodb connection
connectionString = "mongodb+srv://bin:Robin1999@cluster0-qgaoz.mongodb.net/test?retryWrites=true&w=majority"
client = MongoClient(connectionString)
db = client.smartify


# ----------------------- AUTH API PROCEDURE -------------------------

@app.route("/auth")
def auth():
    return redirect(spotify.AUTH_URL)


@app.route("/callback/")
def callback():

    auth_token = request.args['code']
    auth_header = spotify.authorize(auth_token)
    session['auth_header'] = auth_header

    return home()

def valid_token(resp):
    return resp is not None and not 'error' in resp





# HOME PAGE

@app.route("/")
def home():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        profile = spotify.get_users_profile(auth_header)

        if not valid_token(profile):
            return render_template("first.html")


        # LOAD RECENTLY PLAYED SONGS

        recently_played = spotify.get_users_recently_played(auth_header)

        with open('recently_played.json', 'w') as outfile:
            json.dump(recently_played, outfile)

        with open('recently_played.json') as json_file:
            recently_played_data = json.load(json_file)

        #print(recently_played_data)

        song_uris = []
        song_names = []
        played_at = []

        for temp in recently_played_data['items']:
            for key, value in temp.items():
                if (key == 'played_at'):
                    played_at.append(value)
                    #print(value)
                elif (key == 'track'):
                    for k, v in temp['track'].items():
                        if (k == 'uri'):
                            song_uris.append(v)
                            #print(v)
                        elif (k == 'name'):
                            song_names.append(v)
                            #print(v)

        print("trying mongodb")

        # clear database first
        db.recently_played.drop()

        for i in range(len(song_uris)):
            new_song = ({"song_uri": song_uris[i], "song_name": song_names[i], "played_at": played_at[i] })
            db.recently_played.insert_one(new_song)


        # LOAD DATA ON TOP SONGS AND ARTISTS INTO MYSQL DATABASE

        # ARTISTS

        top_artists = spotify.get_users_top(auth_header, 'artists')

        with open('top_artists.json', 'w') as outfile:
            json.dump(top_artists, outfile)

        with open('top_artists.json') as json_file:
            artist_data = json.load(json_file)

        #print(artist_data)

        artist_ids = []
        artist_names = []
        artist_popularity = []
        artist_ratings = []

        count = 0

        for temp in artist_data['items']:
            for key, value in temp.items():
                if (key == 'id'):
                    #print(value)
                    artist_ids.append(value)

                    if (count < 10):
                        artist_ratings.append(5)
                    elif (count < 20):
                        artist_ratings.append(4)
                    elif (count < 30):
                        artist_ratings.append(3)
                    elif (count < 40):
                        artist_ratings.append(2)
                    else:
                        artist_ratings.append(1)

                    count += 1
                elif (key == 'name'):
                    #print(value)
                    artist_names.append(value)
                elif (key == 'popularity'):
                    #print(value)
                    artist_popularity.append(value)

        with engine.connect() as con:
            con.execute("TRUNCATE TABLE top_artists")

            for i in range(len(artist_ids)):
                new_artist = Artist(artist_id = artist_ids[i], artist_name = artist_names[i], popularity = artist_popularity[i], rating = artist_ratings[i])
                SQL_db.session.add(new_artist)
            
            SQL_db.session.commit()



        # SONGS 

        top_songs = spotify.get_users_top(auth_header, 'tracks')

        with open('top_songs.json', 'w') as outfile:
            json.dump(top_songs, outfile)

        with open('top_songs.json') as json_file:
            song_data = json.load(json_file)
        
        #print(song_data)

        song_ids = []
        song_names = []
        artist_names = []
        song_popularity = []
        song_ratings = []

        count = 0

        for temp in song_data['items']:
            for key, value in temp.items():
                #print(key)
                if (key == 'id'):
                    #print(value)
                    song_ids.append(value)

                    if (count < 10):
                        song_ratings.append(5)
                    elif (count < 20):
                        song_ratings.append(4)
                    elif (count < 30):
                        song_ratings.append(3)
                    elif (count < 40):
                        song_ratings.append(2)
                    else:
                        song_ratings.append(1)

                    count += 1
                elif (key == 'name'):
                    #print(value)
                    song_names.append(value)
                elif (key == 'popularity'):
                    #print(value)
                    song_popularity.append(value)
                elif (key == 'artists'):
                    for k, v in temp['artists'][0].items():
                        if (k == 'name'):
                            #print(v)
                            artist_names.append(v)
                            break
    

        with engine.connect() as con:
            con.execute("TRUNCATE TABLE top_songs")

            for i in range(len(song_ids)):
                new_song = Song(song_id = song_ids[i], song_name = song_names[i], artist_name = artist_names[i], popularity = song_popularity[i], rating = song_ratings[i])
                SQL_db.session.add(new_song)
            
            SQL_db.session.commit()


        if valid_token(profile):
            return render_template("first.html",
                                user=profile)
    return render_template("first.html")


@app.route("/recent")
def recent():
    if 'auth_header' in session:
        auth_header = session['auth_header']

        profile = spotify.get_users_profile(auth_header)

        text = ""
        for x in db.recently_played.find({}, {'_id': 0,'song_name': 1, 'played_at': 1}):
            text += pprint.pformat(x)
            text += '\n\n'
        
        if valid_token(profile):
            return render_template("recent.html",
                                user=profile, text = text)
    return render_template("recent.html")



# LIST TOP SONGS AND ARTISTS

@app.route("/list")
def list():
    if 'auth_header' in session:
        auth_header = session['auth_header']

        profile = spotify.get_users_profile(auth_header)


        # DISPLAY CURRENT LIST OF TOP SONGS AND ARTISTS
        with engine.connect() as con:
    
            rows = con.execute('SELECT * FROM top_artists')

            artist_text = ""
            while True:
                row = rows.fetchone()
                if row == None:
                    break
                else:
                    artist_text += str(row)
                    artist_text += "\n"

            artist_text += "\n\n"

            rows = con.execute('SELECT * FROM top_songs')

            song_text = ""
            while True:
                row = rows.fetchone()
                if row == None:
                    break
                else:
                    song_text += str(row)
                    song_text += "\n"
        
            if valid_token(profile):
                return render_template("list.html",
                                user=profile, artist_text = artist_text, song_text = song_text)
    return render_template("list.html")



# INSERT

@app.route("/insert")
def insert():
    # MONGODB: print everything in collection
    #database_text = ""

    #for x in db.friends.find({}):
    #    database_text += pprint.pformat(x)
    #    database_text += '\n\n'



    #count = db.friends.count_documents({})
    #print("TESTTT")
    #print(count)

    #count = db.friends.count_documents({})
    #print("TESTTT")
    #print(count)

    return render_template("insert.html")


@app.route('/insert', methods=['POST'])
def process_insert():
    name = request.form['name']
    rating = request.form['rating']
    search_type = request.form['search_type']

    if 'auth_header' in session:
        auth_header = session['auth_header']
       
        if (search_type == 'artist'):
            data = spotify.search('artist', name, auth_header) 
            result = data['artists']['items']
            print(result[0])

            artist_id = result[0]['id']
            artist_name = result[0]['name']
            popularity = result[0]['popularity']

            new_artist = Artist(artist_id = artist_id, artist_name = artist_name, popularity = popularity, rating = rating)
            SQL_db.session.add(new_artist)
        else:
            data = spotify.search('track', name, auth_header) 
            result = data['tracks']['items']
            print(result[0])

            song_id = result[0]['id']
            song_name = result[0]['name']
            popularity = result[0]['popularity']
            artist_name = ""

            for k, v in result[0]['artists'][0].items():
                if (k == 'name'):
                    artist_name = v
                    break

            new_song = Song(song_id = song_id, song_name = song_name, artist_name = artist_name, popularity = popularity, rating = rating)
            SQL_db.session.add(new_song)

        SQL_db.session.commit()

    return insert()




# SEARCH 

@app.route("/search")
def search():
    return render_template("search.html", text = "")

@app.route('/search', methods=['POST'])
def process_search():
    rating = request.form['rating']
    search_type = request.form['search_type']
    
    # friend = ""
    # for x in db.friends.find({"username": username}):
    #     friend += pprint.pformat(x)
    #     friend += '\n\n'

    with engine.connect() as con:
        command = "SELECT * FROM "

        if (search_type == 'artist'):
            command += "top_artists WHERE rating = '"
        else:
            command += "top_songs WHERE rating = '"
        command += rating
        command += "'"

        rows = con.execute(command)
        #songs = rows.fetchall()

        result = ""
        while True:
            row = rows.fetchone()
            if row == None:
                break
            else:
                result += str(row)
                result += "\n"
    
        return render_template("search.html", text = result)




# UPDATE

@app.route("/update")
def update():
    # MONGODB
    # database_text = ""

    # for x in db.friends.find({}):
    #     database_text += pprint.pformat(x)
    #     database_text += '\n\n'

    # count = db.friends.count_documents({})

    return render_template("update.html")


@app.route('/update', methods=['POST'])
def process_update():
    name = request.form['name']
    rating = request.form['rating']
    search_type = request.form['search_type']

    # MONGODB
    # db.friends.update_one({"username": username},{"$set": {"rating": rating}})

    if (search_type == 'artist'):
        artist = Artist.query.filter_by(artist_name = name).first()

        if artist:
            artist.rating = rating
    else:
        song = Song.query.filter_by(song_name = name).first()

        if song:
            song.rating = rating

    SQL_db.session.commit()

    return update()



# REMOVE

@app.route("/remove")
def remove():
    # MONGODB
    # database_text = ""

    # for x in db.friends.find({}):
    #     database_text += pprint.pformat(x)
    #     database_text += '\n\n'

    # count = db.friends.count_documents({})

    return render_template("remove.html")


@app.route('/remove', methods=['POST'])
def process_remove():
    name = request.form['name']
    search_type = request.form['search_type']

    if (search_type == 'artist'):
        Artist.query.filter_by(artist_name = name).delete()
    else:
        Song.query.filter_by(song_name = name).delete()

    SQL_db.session.commit()

    # MONGODB
    # db.friends.remove( { "username": username } )

    return remove()



@app.route("/query")
def query():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        profile = spotify.get_users_profile(auth_header)

        if not valid_token(profile):
            return render_template("query.html")
        
        with engine.connect() as con:
            rows = con.execute('SELECT top_artists.artist_name, count(*) as song_count FROM top_songs JOIN top_artists on top_songs.artist_name = top_artists.artist_name GROUP BY artist_name ORDER BY song_count desc;')
            #data = rows.fetchall()

            result = ""
            while True:
                row = rows.fetchone()
                if row == None:
                    break
                else:
                    result += str(row)
                    result += "\n"

            rows = con.execute('SELECT song_name, popularity FROM top_songs ORDER BY popularity desc;')

            popularity_result = ""
            while True:
                row = rows.fetchone()
                if row == None:
                    break
                else:
                    popularity_result += str(row)
                    popularity_result += "\n"

            rows = con.execute('SELECT avg(popularity) as avg_popularity FROM top_artists;')
            artist_rating = rows.fetchall()
            artist_rating = str(artist_rating[0])
            artist_rating = artist_rating[10:15]
            print(artist_rating)

            rows = con.execute('SELECT avg(popularity) as avg_popularity FROM top_songs;')
            song_rating = rows.fetchall()
            song_rating = str(song_rating[0])
            song_rating = song_rating[10:15]
            print(song_rating)

            p_rating = (float(artist_rating) + float(song_rating)) / 2.0


    return render_template("query.html", user = profile, current_data = result, popularity_data = popularity_result, artist_rating = artist_rating, song_rating = song_rating, popular_rating = p_rating)




@app.route("/playlist")
def playlist():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        profile = spotify.get_users_profile(auth_header)

        if not valid_token(profile):
            return render_template("playlist.html")

        playlists = spotify.get_users_playlists(auth_header)
 
        with open('playlists.json', 'w') as outfile:
            json.dump(playlists, outfile)

        with open('playlists.json') as json_file:
            playlists = json.load(json_file)

        playlist_names_str = ""

        for temp in playlists['items']:
            for key, value in temp.items():
                if (key == 'name'):
                    playlist_names_str += value
                    playlist_names_str += "\n"

        return render_template("playlist.html", user = profile, text = playlist_names_str)
    return render_template("playlist.html")


@app.route('/playlist', methods=['POST'])
def process_playlist():
    # MONGODB
    # db.friends.remove( { "username": username } )

    name = request.form['name']

    if 'auth_header' in session:
        auth_header = session['auth_header']
        profile = spotify.get_users_profile(auth_header)

        if not valid_token(profile):
            return render_template("playlist.html")


        # PARSE ALL OF USER'S PUBLIC PLAYLISTS
        playlists = spotify.get_users_playlists(auth_header)

        with open('playlists.json', 'w') as outfile:
            json.dump(playlists, outfile)

        with open('playlists.json') as json_file:
            playlists = json.load(json_file)

        playlist_names = []
        playlist_ids = []
        playlist_names_str = ""

        for temp in playlists['items']:
            for key, value in temp.items():
                #print(key)
                if (key == 'name'):
                    playlist_names.append(value)
                    playlist_names_str += value
                    playlist_names_str += "\n"
                elif (key == 'id'):
                    playlist_ids.append(value)

        result = "playlist not found!"
        playlist_id = ""
        for index in range(len(playlist_names)):
            if (playlist_names[index] == name):
                result = "done!"
                playlist_id = playlist_ids[index]
                break

        if result == "playlist not found!":
            return render_template("playlist.html", user = profile, text = playlist_names_str, result = result)


        # PARSE PLAYLIST TRACKS

        # get track ids of all tracks in playlist
        playlist_tracks = spotify.get_playlist_tracks(auth_header, playlist_id)

        with open('playlist_tracks.json', 'w') as outfile:
            json.dump(playlist_tracks, outfile)

        with open('playlist_tracks.json') as json_file:
            playlist_tracks = json.load(json_file)

        track_uris = []

        for temp in playlist_tracks['items']:
            for key, value in temp.items():
                if (key == 'track'):
                    for k, v in temp[key].items():
                        if (k == 'uri'):
                            track_uris.append(v)
                            break
        
        # loop through all track ids

        for current_uri in track_uris:
            # search mongodb database for track id

            found = ""   # CHANGEeEeeeeeeeeeee

            for x in db.recently_played.find({"song_uri": current_uri}):
                found += pprint.pformat(x)
                found += '\n\n'
            
            if (found == ""):
                # if not found, remove track id from playlist
                
                spotify.remove_track_from_playlist(auth_header, playlist_id, current_uri)
                print("NOT FOUND")
                
                with engine.connect() as con:
                    # get random track from current top 50 songs
                    rows = con.execute('SELECT song_id from top_songs order by rand() limit 1;')
                    song_id = rows.fetchall()
                    song_id = str(song_id)[3:25]

                    # use song as seed for spotify recommendation
                    recommendations = spotify.get_track_recommendation(auth_header, song_id)
            
                    # use recommendation to replace the old song
                    for temp in recommendations['tracks']:
                        for key, value in temp.items():
                            if (key == 'uri'):
                                song_rec_uri = value
                                spotify.add_track_to_playlist(auth_header, playlist_id, song_rec_uri)
                                break

        
        return render_template("playlist.html", user = profile, text = playlist_names_str, result = result)

    return playlist()

if __name__ == "__main__":
    app.run(debug=True)
 