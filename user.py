import base64
import json

# returns the user's id (from the FB cookie)
def parseSignedRequest(sr):
    [encoded_signiture, payload] = sr.split('.')
    encoded_signiture = encoded_signiture + "="*(4 - len(encoded_signiture) % 4)
    payload = payload + "="*(4-len(payload) % 4)

    # signiture = base64.urlsafe_b64decode(str(encoded_signiture))
    data = json.loads(base64.urlsafe_b64decode(str(payload)))
    return data['user_id']

def nameFromId(id, mongo):
    user = ""
    try:
        user = mongo.db.users.find({'_id': id})[0]
    except:
        return "BANANA"
    name = user['name']
    return "%s %s" % (name['first'], name['last'])
