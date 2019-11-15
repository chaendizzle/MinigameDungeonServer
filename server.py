from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import hashlib
import random
import binascii
import os
from flask import Flask, session, redirect, render_template
from flask import request, abort, jsonify
from flask_session import Session
import time
from datetime import datetime
import textwrap
import re
from validate_email import validate_email

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
DEV_SPREADSHEET_ID = '1sy5psgH_hUcdbhi6a5oxod1yQ8d0oKCNK58fMSS7duA'
PROD_SPREADSHEET_ID = '1vctIy_JQoMc1MDxmxe0NXO-vbSC43yJO_sw9eQ3k4yM'
SIGNUP_RANGE = 'Form Responses 1!A2:B'

SPREADSHEET = None

app = Flask(__name__)

SIGNUP_DEFAULT_ROW = ['', '']

EMAIL_REGEX = """(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""

EMAIL_PATTERN = None

# if in development mode, use development spreadsheet.
# otherwise, use production spreadsheet.
DEV_MODE = True
SPREADSHEET_ID = DEV_SPREADSHEET_ID
if not DEV_MODE:
    SPREADSHEET_ID = PROD_SPREADSHEET_ID

def append(sheet_range, rows):
    body = {
        'majorDimension': 'ROWS',
        'values': rows
    }
    SPREADSHEET.values().append(spreadsheetId=SPREADSHEET_ID, range=sheet_range,
                                valueInputOption='USER_ENTERED',
                                insertDataOption='INSERT_ROWS',
                                body=body).execute()

def update(sheet_range, rows):
    body = {
        "values": rows
    }
    SPREADSHEET.values().update(spreadsheetId=SPREADSHEET_ID, range=sheet_range,
                                valueInputOption='USER_ENTERED',
                                body=body).execute()

def fetch(sheet_range, default_row):
    result = SPREADSHEET.values().get(spreadsheetId=SPREADSHEET_ID,
                                      range=sheet_range).execute()
    # pad entries to correct size
    entries = result.get('values', [])
    for row in entries:
        if len(row) < len(default_row):
            for i in range(len(row), len(default_row)):
                row.append(default_row[i])
    return entries

def main():
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
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    global SPREADSHEET
    SPREADSHEET = service.spreadsheets()

    # compile the email regex pattern
    global EMAIL_PATTERN
    EMAIL_PATTERN = re.compile(EMAIL_REGEX)

"""
WEB ROUTE METHODS
"""
@app.route('/', methods=['GET'])
def index():
    return 'The web server is up and running.'

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # get email
    email = None
    if request.method == 'POST':
        email = request.form.get('email')
    elif DEV_MODE:
        email = request.args.get('email')
    if not email:
        print('No email provided in request.')
        abort(404)
        return
    # remove all equals signs from beginning to prevent google sheets injection
    email = str(email).lstrip('=').strip()
    # check that the email is a UW student email
    if not email.endswith('@wisc.edu') or not re.match(EMAIL_PATTERN, email): 
        print('Email ' + email + ' is not a valid UW email.')
        abort(400)
        return
    # verify email with wisc.edu servers via SMTP
    is_valid = validate_email(email_address=email, smtp_timeout=3)
    if not is_valid:
        print('Email ' + email + ' is not an existing UW email.')
        abort(406)
        return
    # verify that the email is unique in the spreadsheet
    users = fetch(SIGNUP_RANGE, SIGNUP_DEFAULT_ROW)
    for user in users:
        if email.strip() == user[1].strip():
            print('Duplicate email %s, rejecting.' % email)
            abort(422)
            return
    # append the email to the spreadsheet
    now = datetime.now()
    append(SIGNUP_RANGE, [[now.strftime('%m/%d/%Y %H:%M:%S'), email]])
    print('Valid email %s received, appending to spreadsheet.' % email)
    return ''

main()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=42069)
