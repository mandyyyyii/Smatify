import pymongo
from flask import Flask, render_template, request  
from pymongo import MongoClient

app = Flask(__name__)

@app.route("/")
def home():
    connectionString = "mongodb+srv://bin:Robin1999@cluster0-qgaoz.mongodb.net/test?retryWrites=true&w=majority"
    client = MongoClient(connectionString)
    db = client.smartify
    #collection = db.users

    # EXAMPLE DOCUMENT
    test = ({"name": "Hannah", "password": "12345", "age": 19 })

    # INSERT
    #db.users.insert_one(test)

    # REMOVE
    #db.users.remove( { "_id": 1 } )

    # UPDATE
    #db.users.update_one({"name": "old_name"},{"$set": {"name": "new_name"}})
    
    # print everything in collection
    for x in db.users.find({}):
        print(x)

    # print number of things in collection
    count = db.users.count_documents({})
    print(count)

    #if "open" in request.form:
    #    print("open pressed")
    #elif "close" in request.form:
    #    print("close pressed")

    return render_template("first.html", num = count)

    
#@app.route("/about")
#def about():
#    return render_template("about.html")

@app.route("/insert")
def insert():
    return render_template("insert.html")
    
@app.route("/search")
def search():
    return render_template("search.html")


@app.route("/update")
def update():
    return render_template("update.html")

@app.route("/remove")
def remove():
    return render_template("remove.html")



if __name__ == "__main__":
    app.run(debug=True)
 