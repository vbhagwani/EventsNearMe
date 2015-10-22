from flask import Flask
from flask import request
from flask.ext.pymongo import PyMongo
from flask import session
from flask import render_template, abort, jsonify, request

import facebook
import base64
import json
import pprint
from bson.json_util import dumps

from event import *
from forms import *

app = Flask("mydb")
app.debug = True
mongo = PyMongo(app)


# returns the user's id (from the FB cookie)
def parseSignedRequest(sr):
    [encoded_signiture, payload] = sr.split('.')
    encoded_signiture = encoded_signiture + "="*(4 - len(encoded_signiture) % 4)
    payload = payload + "="*(4-len(payload) % 4)

    # signiture = base64.urlsafe_b64decode(str(encoded_signiture))
    data = json.loads(base64.urlsafe_b64decode(str(payload)))
    return data['user_id']


def checkLoggedIn():
    if request.cookies.get('fbsr_1055849787782314') != None:
        session['logged_in'] = True
        user_id = parseSignedRequest(request.cookies.get('fbsr_1055849787782314'))

        user = mongo.db.users.find({'_id': user_id})[0]
        name = user['name']
        session['name'] = "%s %s" % (name['first'], name['last'])

        session.modified = True

    else:
        session['logged_in'] = False
        session.modified = True

@app.route("/")
def hello():
    checkLoggedIn() # must be called in each view
    return render_template("map.html", events=constructTestEvents(mongo))


@app.route("/event/<eventid>")
def event(eventid):
    checkLoggedIn()
    event = getEvent(mongo, eventid)
    if event == None:
        abort(404)
    return render_template("event.html", event=event)


@app.route("/events/")
def events():
    checkLoggedIn()
    return render_template("eventsList.html", events=constructTestEvents(mongo))

@app.route("/create", methods=['GET', 'POST'])
def createEvent():
    form = createEventForm(request.form)
    checkLoggedIn()
    if request.method == 'POST' and form.validate():
        print "#############"
    return render_template("create_event.html", form=form)

@app.errorhandler(404)
def page_not_found(error):
    checkLoggedIn()
    msgs = ["Sorry", "Whoops", "Uh-oh", "Oops!", "You broke it.", "You done messed up, A-a-ron!"]
    choice = random.choice(msgs) #choose one randomly from above
    return render_template('page_not_found.html', choice=choice), 404

@app.route("/login")
def users():
	uid = request.args.get("uid")
	name = request.args.get("name")
	cursor = mongo.db.users.find( {"_id": uid} )
	if cursor.count() == 1:
		return dumps("FOUND IN DB")
	else:
		result = mongo.db.users.insert_one(
			{
				"_id": uid,
				"name": {
					"first": name.split(' ')[0],
					"last": name.split(' ')[1]
				},
				"age": 999,
				"email" : "test@test.com"
			})
		return dumps("ADDED TO DB")

if __name__ == "__main__":
    app.secret_key = 'supersecretsecretkey'
    app.run()
