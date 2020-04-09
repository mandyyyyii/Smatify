import pymongo
import pprint
from flask import Flask, flash, render_template, request, redirect
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "super secret key"

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
    # print everything in collection
    database_text = ""

    for x in db.friends.find({}):
        database_text += pprint.pformat(x)
        database_text += '\n\n'

    count = db.friends.count_documents({})
    
    return render_template("insert.html", text = database_text, num = count)


@app.route('/insert', methods=['POST'])
def process_insert():
    username = request.form['username']
    name = request.form['name']
    rating = request.form['rating']

    new_friend = ({"username": username, "name": name, "rating": rating })

    db.friends.insert_one(new_friend)

    return insert()


# SEARCH 

@app.route("/search")
def search():
    return render_template("search.html", text = "")

@app.route('/search', methods=['POST'])
def process_search():
    username = request.form['username']
    
    friend = ""
    for x in db.friends.find({"username": username}):
        friend += pprint.pformat(x)
        friend += '\n\n'
    
    return render_template("search.html", text = friend)




# UPDATE

@app.route("/update")
def update():
    database_text = ""

    for x in db.friends.find({}):
        database_text += pprint.pformat(x)
        database_text += '\n\n'

    count = db.friends.count_documents({})

    return render_template("update.html", text = database_text, num = count)

@app.route('/update', methods=['POST'])
def process_update():
    username = request.form['username']
    rating = request.form['rating']

    db.friends.update_one({"username": username},{"$set": {"rating": rating}})

    return update()



# REMOVE

@app.route("/remove")
def remove():
    database_text = ""

    for x in db.friends.find({}):
        database_text += pprint.pformat(x)
        database_text += '\n\n'

    count = db.friends.count_documents({})

    return render_template("remove.html", text = database_text, num = count)


@app.route('/remove', methods=['POST'])
def process_remove():
    username = request.form['username']

    db.friends.remove( { "username": username } )

    return remove()


if __name__ == "__main__":
    app.run(debug=True)
 