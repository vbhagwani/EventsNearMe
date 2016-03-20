# manage.py

from flask.ext.script import Manager, prompt, prompt_pass
from server import app
from pymongo import MongoClient
import uuid
import md5

manager = Manager(app)


@manager.command
def hello(name):
    "just say hello"
    print "hello"


@manager.command
def createAdmin():
    "Create an Admin User"
    print "Creating Admin User..."
    fname = prompt(name="First Name")
    lname = prompt(name="Last Name")
    email = prompt(name="Email")
    password = prompt_pass(name="password")

    name = {"last": lname,
            "first": fname}

    client = MongoClient()
    db = client.mydb
    users = db.users

    uid = str(uuid.uuid4())
    salt = str(uuid.uuid4())
    m = md5.md5()
    m.update(unicode(salt)+password)
    hashed = m.hexdigest()

    admin = {
        "_id": uid,
        "hash": hashed,
        "name": name,
        "admin": False,
        "salt": salt,
        "email": email,
        "admin": True,
        "tags": [],
        "picture": "http://lorempixel.com/g/250/250/"
    }

    users.insert_one(admin)

if __name__ == "__main__":
    manager.run()
