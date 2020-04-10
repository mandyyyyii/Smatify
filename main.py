import pymongo
import pprint
import pymysql
from flask import Flask, flash, render_template, request, redirect
from pymongo import MongoClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.sql import text



app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:cs411project@localhost/smartify'
SQL_db = SQLAlchemy(app)

class Friend(SQL_db.Model):

    __tablename__ = 'Friends'

    username = SQL_db.Column(SQL_db.String(150), nullable=False, primary_key=True)
    name = SQL_db.Column(SQL_db.String(150), nullable=False)
    rating = SQL_db.Column(SQL_db.Integer, nullable=False)


# SQL connection
engine = create_engine('mysql+pymysql://root:cs411project@localhost/smartify')

# mongodb connection
connectionString = "mongodb+srv://bin:Robin1999@cluster0-qgaoz.mongodb.net/test?retryWrites=true&w=majority"
client = MongoClient(connectionString)
db = client.smartify


# HOME PAGE
@app.route("/")
def home():
    return render_template("first.html")



# INSERT

@app.route("/insert")
def insert():
    # MONGODB: print everything in collection
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

        return render_template("insert.html", text = data, num = final_count)


@app.route('/insert', methods=['POST'])
def process_insert():
    username = request.form['username']
    name = request.form['name']
    rating = request.form['rating']

    new_friend = Friend(username = username, name = name, rating = rating)
    SQL_db.session.add(new_friend)
    SQL_db.session.commit()

    return insert()


# SEARCH 

@app.route("/search")
def search():
    return render_template("search.html", text = "")

@app.route('/search', methods=['POST'])
def process_search():
    rating = request.form['rating']
    
    # friend = ""
    # for x in db.friends.find({"username": username}):
    #     friend += pprint.pformat(x)
    #     friend += '\n\n'

    with engine.connect() as con:
        command = "SELECT * FROM friends WHERE rating = '"
        command += rating
        command += "'"

        rows = con.execute(command)
        friend = rows.fetchall()
    
    return render_template("search.html", text = friend)




# UPDATE

@app.route("/update")
def update():
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

    return render_template("update.html", text = data, num = final_count)


@app.route('/update', methods=['POST'])
def process_update():
    username = request.form['username']
    rating = request.form['rating']

    # MONGODB
    # db.friends.update_one({"username": username},{"$set": {"rating": rating}})

    friend = Friend.query.filter_by(username = username).first()
    if friend:
        friend.rating = rating
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

    return render_template("remove.html", text = data, num = final_count)


@app.route('/remove', methods=['POST'])
def process_remove():
    username = request.form['username']

    # MONGODB
    # db.friends.remove( { "username": username } )

    Friend.query.filter_by(username = username).delete()
    SQL_db.session.commit()

    return remove()


if __name__ == "__main__":
    app.run(debug=True)
 