#!/usr/bin/env python

from __future__ import print_function
import httplib2
import os
import pycurl
import urllib
import json

from StringIO import StringIO
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from datetime import datetime

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Sheets API Updater'

SPREADSHEETID = '1rMa9fBXew4sikGe0OqNrlgOfWUYxy8PR9Ibdb8Os_dY'
RANGENAME = 'Sheet1!U2:5'

URL = \
    "https://graph.facebook.com/v2.8/me/posts" \
    "fields=created_time%2Cfrom%2Cmessage%2Ccomments%7Bmessage%2Cattachment%2Ccreated_time%2Cfrom%2C" \
    "comments%7Bmessage%2Cattachment%2Ccreated_time%2Cfrom%7D%7D&access_token="

URL = \
 "https://graph.facebook.com/v2.8/me/posts?fields=created_time%2Cfrom%2Cmessage%2Ccomments%7Bmessage%2Cattachment%2Ccreated_time%2Cfrom%7D&access_token="

URL = URL.replace(" ", "")


def now():
    return datetime.strftime(datetime.now(), "%Y-%m-%dT%H.%M.%S")

def exToken(token):

    URL = "https://graph.facebook.com/oauth/access_token?client_id=1817269595199991&client_secret=86279e2102865535aa596bd9219862ef&grant_type=fb_exchange_token&fb_exchange_token=" + token

    #print (URL)
    buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, URL)
    #c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.WRITEFUNCTION, buffer.write)
    c.perform()
    c.close()

    body = buffer.getvalue()
    t, e = body.split("&")
    token = t.split("=")[1]
    return token

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

def getFB(token):
    buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, URL + token)
    #c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.WRITEFUNCTION, buffer.write)
    #c.setopt(c.VERBOSE, True)

    c.perform()
    c.close()

    body = buffer.getvalue()
    # Body is a string in some encoding.
    # In Python 2, we can print it without knowing what the encoding is.
    body = json.loads(body)

    text = ""
    post = ""
    comm = []
    for line in body["data"]:
        #print (line)
        message = line.get("message")

        if message:
            d = datetime.strptime(line.get("created_time")[:19], '%Y-%m-%dT%H:%M:%S')
            post = "%d.%d. %d:%d - %s\n" % (d.day, d.month, d.hour, d.minute, message)

            comments = line.get("comments")
            if comments:
                for comment in line["comments"]["data"]:
                    at = comment.get("attachment")
                    #print (at)
                    attachment = ''
                    if at:
                        attachment = "  :-)  "# % at['media']['image']['src']
                    msg = \
                        "%s: %s %s" % (
                            comment.get("from")['name'],
                            comment.get("message"),
                            attachment)
                    comm.append(msg)

                    #print (msg)
                    reply = comment.get("comments")
                    if reply:
                        for line in reply.get("data"):
                            attachment = ''
                            if at:
                                attachment = "  :-)  "# % at['media']['image']['src']
                            msg = \
                                "   %s: %s %s" % (
                                comment.get("from")['name'],
                                comment.get("message"),
                                attachment)
                            comm.append(msg)
        break

    print ("%s: Readet %d comments from FB" % (now(), len(comm)))
    return post, comm


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main(token):
    post, comm = getFB(token)
    comm.reverse()
    comm = comm[:10]
    text = "\n\n".join(comm)

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    values = [
        [post], [], [], [text]
    ]
    body = {
        'values': values
    }
    print ("%s: update %d values in G docs" % (now(), len(values)))
    return service.spreadsheets().values().update(
        spreadsheetId = SPREADSHEETID, range = RANGENAME, valueInputOption='RAW', body=body).execute()

if __name__ == '__main__':
    f = open("fbtoken", 'r+')
    lasttoken = f.readline().strip()
    token = exToken(lasttoken)
    f.seek(0)
    f.truncate()
    f.write(token)
    main(token)
    f.close()
