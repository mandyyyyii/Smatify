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

try:
    import configparser
except:
    from six.moves import configparser



app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:cs411project@localhost/smartify'
SQL_db = SQLAlchemy(app)

class Friend(SQL_db.Model):

    __tablename__ = 'Friends'

    username = SQL_db.Column(SQL_db.String(150), nullable=False, primary_key=True)
    name = SQL_db.Column(SQL_db.String(150), nullable=False)
    rating = SQL_db.Column(SQL_db.Integer, nullable=False)

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


        # LOAD DATA ON TOP SONGS AND ARTISTS INTO MYSQL DATABASE

        # ARTISTS

        top_artists = spotify.get_users_top(auth_header, 'artists')

        with open('top_artists.json', 'w') as outfile:
            json.dump(top_artists, outfile)

        with open('top_artists.json') as json_file:
            artist_data = json.load(json_file)

        artist_ids = []
        artist_names = []
        artist_popularity = []
        artist_ratings = []

        count = 0

        for temp in artist_data['items']:
            for key, value in temp.items():
                if (key == 'uri'):
                    print(value)
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
                    print(value)
                    artist_names.append(value)
                elif (key == 'popularity'):
                    print(value)
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

        song_ids = []
        song_names = []
        song_popularity = []
        song_ratings = []

        count = 0

        for temp in song_data['items']:
            for key, value in temp.items():
                if (key == 'uri'):
                    print(value)
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
                    print(value)
                    song_names.append(value)
                elif (key == 'popularity'):
                    print(value)
                    song_popularity.append(value)
    

        with engine.connect() as con:
            con.execute("TRUNCATE TABLE top_songs")

            for i in range(len(song_ids)):
                new_song = Song(song_id = song_ids[i], song_name = song_names[i], popularity = song_popularity[i], rating = song_ratings[i])
                SQL_db.session.add(new_song)
            
            SQL_db.session.commit()


        if valid_token(profile):
            return render_template("first.html",
                                user=profile)
    return render_template("first.html")



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

    print(name)

    if 'auth_header' in session:
        auth_header = session['auth_header']

        access_token = auth_header['Authorization']
        access_token = access_token[7:]
        print(access_token)

        artist = spotify.search('artist', name, access_token) 
        print(artist)

        #if valid_token(profile):
        #    return render_template("first.html", user=profile)
    

    #new_friend = Friend(username = username, name = name, rating = rating)
    #SQL_db.session.add(new_friend)
    #SQL_db.session.commit()

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

    with engine.connect() as con:
    
        rows = con.execute('SELECT * FROM friends')
        data = rows.fetchall()

        count = con.execute('SELECT COUNT(*) FROM friends')
        final_count = count.fetchall()

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


if __name__ == "__main__":
    app.run(debug=True)
 