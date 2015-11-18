# flask imports
from flask.ext.pymongo import PyMongo
from flask import Flask, request, render_template, abort, jsonify, redirect, url_for, session
# base python imports
import json
import uuid
import random
from bson.json_util import dumps
from datetime import datetime
# EventsNear.me imports
from event import *
from user import *
from forms import *
from form_parsers import *

# start flask server
app = Flask("mydb")
app.debug = True
# connect to the pymongo server
mongo = PyMongo(app)


# the main map page
@app.route("/")
def map():
    checkLoggedIn(mongo)  # must be called in each view
    return render_template("map.html", events=generateEvents(mongo))


# the event list page
@app.route("/events/", methods=['GET', 'POST'])
def events():
    if request.method == "POST":
        print "POSTED"
        for i in request.form:
            print request.form[i]

        if len(str(request.form["tags2"])) == 0:
            tags = ""
        else:
            tags = str(request.form['tags2']).split(',')
            for i in range(0, len(tags)):
                # strip each element of whitespace and convert to lowercase
                tags[i] = tags[i].strip().lower()

        st = datetime.strptime(request.form["startdt"], "%a, %d %b %Y %H:%M:%S %Z")
        end = datetime.strptime(request.form["enddt"], "%a, %d %b %Y %H:%M:%S %Z")

        cursor = performQuery(st, end, request.form["radius2"], request.cookies.get("lat"), request.cookies.get("lng"), tags)
        ev = []
        for c in cursor:
            print c
            ev.append(Event(c['_id'], mongo))
        return render_template("eventsList.html", events=ev)

    checkLoggedIn(mongo)
    return render_template("eventsList.html", events=generateEvents(mongo))


# the My Events page (list of all events the user created or is attending)
@app.route("/myevents")
def myevents():
    loggedIn = checkLoggedIn(mongo)  # ensure the user is currently logged in
    if not loggedIn:
        return redirect(url_for('map'))  # redirect to the main page if not

    uid = session['uid']

    created = []
    attending = []

    cursor = mongo.db.events.find({"creator_id": uid})
    for c in cursor:
        created.append(Event(c['_id'], mongo))

    cursor = mongo.db.events.find({
        "attending": session['uid']
    })
    for c in cursor:
        attending.append(Event(c['_id'], mongo))

    return render_template("myevents.html", created=created, attending=attending)


# event specific pages
@app.route("/event/<eventid>", methods=['GET', 'POST'])
def event(eventid):
    loggedIn = checkLoggedIn(mongo)
    event = Event(eventid, mongo)
    if event is None:
        abort(404)  # the given eventid doesn't exist, 404

    # check if the user is currently attending
    session['attending'] = (session['uid'] in event.attending_ids)
    session.modified = True
    form = commentForm(request.form)
    print request.form
	
    if('msg' not in request.form and len(request.form) > 0):
		print request.form
		print request.form.keys()[0]
		itemname = request.form['value'];
		itempos = request.form['index'];
		itempos = str(int(itempos) - 1)
		print itempos
		query = 'items.' + (itempos)+ '.user';
		print query
		if request.form['value'] != "":
			mongo.db.events.update({ '_id': eventid},{'$set' : {query:session['uid']}})
		else:
			mongo.db.events.update({ '_id': eventid},{'$set' : {query:""}})
			
			
    else:
		if request.method == 'POST' and loggedIn:
			if form.validate():
				comment = parseComment(form)
				mongo.db.events.update(
					{"_id": eventid},
					{"$addToSet": {"comments": comment}}
				)
	# need to get the event again since we changed it
    event = Event(eventid, mongo)

    # this page needs access to all of the attending user objects
    event.fillAttendees(mongo)
    return render_template("event.html", event=event, form=form,uid = session['uid'])


# route to join an event
@app.route("/join/<eventid>")
def join(eventid):
    loggedIn = checkLoggedIn(mongo)  # ensure the user is currently logged in
    if not loggedIn:
        return redirect(url_for('map'))  # redirect to the main page if not

    event = Event(eventid, mongo)  # get the event from the DB
    if event is None:
        abort(404)  # if the event doesn't exist, 404

    attending = []
    # if the attendance list is a list, there's already people attending
    if type(event.attending_ids) == list:
        attending = event.attending_ids
        # need to check if this user is already attending before adding them
        if session['uid'] not in event.attending_ids:
            attending.append(session['uid'])
    else:
        # no one is attending yet, so just add this user
        attending.append(session['uid'])

    # update the db with the new attending list
    mongo.db.events.update(
        {"_id": eventid},
        {"$set": {"attending": attending}}
    )

    # return to the event page for this event
    return redirect(request.referrer)


# route to leave an event
@app.route("/leave/<eventid>")
def leave(eventid):
    loggedIn = checkLoggedIn(mongo)  # ensure the user is currently logged in
    if not loggedIn:
        return redirect(url_for('map'))  # redirect to main page if not

    event = Event(eventid, mongo)  # get the evnet from the DB
    if event is None:
        abort(404)  # if the event doesn't exist, 404

    attending = []
    if type(event.attending_ids) == list:
        # set the new attendance list to the current one
        attending = event.attending_ids
        if session['uid'] in event.attending_ids:
            # remove the current user's id if it exists in the list
            attending = attending.remove(session['uid'])

    # update the DB if it changed
    if attending != event.attending_ids:
        mongo.db.events.update(
            {"_id": eventid},
            {"$set": {"attending": attending}}
        )

    # return to the event page for this event
    return redirect(request.referrer)


@app.route("/remove/<eventid>")
def remove(eventid):
    loggedIn = checkLoggedIn(mongo)  # ensure the user is currently logged in
    if not loggedIn:
        return redirect(url_for('map'))  # redirect to main page if not

    event = Event(eventid, mongo)  # get the event so we can see its owner

    if session['uid'] == event.creator.id:  # if the owner is not this user, they can't delete it
        mongo.db.events.remove({"_id": eventid})

    if "/event/" in request.referrer:
        return redirect(url_for('map'))
    return redirect(request.referrer)


# route for creating an event
@app.route("/create", methods=['GET', 'POST'])
def createEvent():
    loggedIn = checkLoggedIn(mongo)  # ensure the user is logged in
    if not loggedIn:
        return redirect(url_for('map'))

    form = createEventForm(request.form)  # load the createEvent form

    # if we got here with a http POST, we are trying to add an event
    if request.method == 'POST':
        if form.validate():  # validate the form data that was submitted
            event = parseEvent(form)
            # insert the event into the DB
            mongo.db.events.insert_one(event)
            # redirect the user to the main map page
            return redirect(url_for('event', eventid=event['_id']))
    # load the create event page if we are loading from a http GET
    # OR if we're loading from a http POST and there was problems with the info
    return render_template("create_event.html", form=form)


# route for editing an Event
@app.route("/edit/<eventid>", methods=['GET', 'POST'])
def editEvent(eventid):
    loggedIn = checkLoggedIn(mongo)  # ensure the user is logged in
    if not loggedIn:
        return redirect(url_for('map'))

    form = createEventForm(request.form)  # load the createEvent form
    # if we got here with a http POST, we are trying to add an event
    if request.method == 'POST':
        if form.validate():  # validate the form data that was submitted
            event = parseEvent(form, eventid)
            print event
            event.pop("_id", None)
            print event
            # insert the event into the DB
            mongo.db.events.update(
                {"_id": eventid},
                event
            )
            # redirect the user to the main map page
            return redirect(url_for('event', eventid=eventid))
        else:
            print "NOT VALIDATED"
    elif request.method == 'GET':
        event = Event(eventid, mongo)
        fillEventForm(form, event)
    # load the create event page if we are loading from a http GET
    # OR if we're loading from a http POST and there was problems with the info
    return render_template("edit_event.html", form=form, eventid=eventid)


# the page that will load for any 404s that are called
@app.errorhandler(404)
def page_not_found(error):
    checkLoggedIn(mongo)
    msgs = ["Sorry", "Whoops", "Uh-oh", "Oops!",
            "You broke it.", "You done messed up, A-a-ron!"]
    choice = random.choice(msgs)  # choose one randomly from above
    return render_template('page_not_found.html', choice=choice), 404


# the login view
@app.route("/login")
def users():
    uid = request.args.get("uid")
    name = request.args.get("name")
    cursor = mongo.db.users.find({"_id": uid})
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
                "email": "test@test.com"
            })
        return dumps("ADDED TO DB")


def performQuery(start, end, r, lat, lng, tags):
    print len(tags)
    if(len(tags) == 0):
        cursor = mongo.db.events.find({
            "start_date": {"$gte": start},
            "end_date": {"$lte": end},
            "location.loc": {
                "$geoWithin": {
                    "$centerSphere": [
                        [float(lng), float(lat)],
                        float(r)/3963.2
                    ]
                }
            }
        })
    else:
        cursor = mongo.db.events.find({
            "start_date": {"$gte": start},
            "end_date": {"$lte": end},
            "tags": {'$in': tags},
            "location.loc": {
                "$geoWithin": {
                    "$centerSphere": [
                        [float(lng), float(lat)],
                        float(r)/3963.2
                    ]
                }
            }
        })
    return cursor


# Filter route to perform database query
@app.route("/filter")
def filter():
    # get AJAX arguments
    startTime = request.args.get("start")
    endTime = request.args.get("end")
    radius = request.args.get("radius").strip()
    lat = request.cookies.get('lat').strip()
    lon = request.cookies.get('lng').strip()
    startdt = datetime.strptime(startTime, "%a, %d %b %Y %H:%M:%S %Z")
    enddt = datetime.strptime(endTime, "%a, %d %b %Y %H:%M:%S %Z")
    tags = request.args.get("tags")
    filters = json.loads(tags)

    cursor = performQuery(startdt, enddt, radius, lat, lon, filters)

    toSend = []
    for i in cursor:
        toSend.append(i)

    return dumps(toSend)

@app.route("/channel")
def channel():
    return render_template("channel.html")


if __name__ == "__main__":
    app.secret_key = 'supersecretsecretkey'
    app.run()
