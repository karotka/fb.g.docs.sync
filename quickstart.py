from __future__ import print_function

#!/usr/bin/env python2.7

import httplib2
import os
import pycurl
import urllib
import json
from datetime import datetime

from StringIO import StringIO


import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1ptVh9j6TX4GbiTJizEtBZ_YLgwUgzjdWQ1PpXWfJBGs'
SAMPLE_RANGE_NAME = 'Sobota 30.3.2019!U2:5'


URL = \
    "https://graph.facebook.com/v2.8/me/posts" \
    "fields=created_time%2Cfrom%2Cmessage%2Ccomments%7Bmessage%2Cattachment%2Ccreated_time%2Cfrom%2C" \
    "comments%7Bmessage%2Cattachment%2Ccreated_time%2Cfrom%7D%7D&access_token="

URL = \
 "https://graph.facebook.com/v2.8/me/posts?fields=created_time%2Cfrom%2Cmessage%2Ccomments%7Bmessage%2Cattachment%2Ccreated_time%2Cfrom%7D&access_token="

URL = \
 "https://graph.facebook.com/v3.2/1003457766464686/posts?limit=1&access_token="
URL = URL.replace(" ", "")


def now():
    return datetime.strftime(datetime.now(), "%Y-%m-%dT%H.%M.%S")

def exToken(token):

    URL = "https://graph.facebook.com/oauth/access_token?client_id=1817269595199991&client_secret=86279e2102865535aa596bd9219862ef&grant_type=fb_exchange_token&fb_exchange_token=" + token

    buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, URL)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()

    body = buffer.getvalue()
    t, e = body.split("&")
    token = t.split("=")[1]
    return token

def getLastPost(token):
    url = "https://graph.facebook.com/v3.2/1003457766464686/posts?limit=1&access_token=" + token
    buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, buffer.write)
    c.perform()
    c.close()

    body = buffer.getvalue()
    body = json.loads(body)

    return body.get("data")

def getComments(token, messageId):
    url = "https://graph.facebook.com/v3.2/" + messageId +"/comments?fields=message,from,created_time&order=reverse_chronological&total_count=10&access_token=" + token
    buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, buffer.write)
    c.perform()
    c.close()

    body = buffer.getvalue()
    body = json.loads(body)
    return body.get("data")

def getFB(token):
    post = getLastPost(token)
    messageId = post[0]["id"]
    postName = post[0]["message"]

    print ("Message id: %s" % messageId)
    comments = getComments(token, messageId)

    text = ""
    post = ""
    comm = []
    for line in comments:
        message = line.get("message")
        fr = line.get("from").get("name")
        d = datetime.strptime(line.get("created_time")[:19], '%Y-%m-%dT%H:%M:%S')
        post = "%d.%d. %d:%d (%s)\n%s\n" % (d.day, d.month, d.hour, d.minute, fr, message)
        comm.append(post)

    print ("%s: Readet %d comments from FB" % (now(), len(comm)))
    print (comm)
    return postName, comm

def getService():

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('sheets', 'v4', credentials=creds)


def main():
    fbToken = "EAAZA0zAyu2fcBAJF2amqT9wfEiPslulJIojtAbDZCTYo4bdFb0vvUwZACKaE7OxPR1d3h1NRdzLQSueuycVIQtVYrMkMMbKo6KXjmGvMRYaZBWIf0ktQLPAZCt7bsOFjJQ0aXQEx72FXDxVHZAFMNxQuVv75rUQosz0Sh5VeqcZBwZDZD"
    postName, comm = getFB(fbToken)
    add = "".join(comm)
    text = postName + "\n\n" + add

    service  = getService()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()

    values = [
        [text],[],[],
        ["test1"]
    ]
    body = {
        'values': values
    }
    print ("%s: update %d values in G docs" % (now(), len(values)))
    return service.spreadsheets().values().update(
        spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME, valueInputOption='RAW', body=body).execute()

if __name__ == '__main__':
    main()
