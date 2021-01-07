# Joshua Moody for Design Engineering SIoT module
# January 2021

# Imports for Google Spreadsheets
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

#Other imports
import serial # for reading from USB
import time
from datetime import datetime

#### Setting up to use Google Sheets API ####
# Scope of permissions required
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# The ID of the spreadsheet.
spreadsheet_id = '1A24Y1SYIFnIcBoFuPChf3bq4sZSUGBj5PF7Pp4J_ETQ'
creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first time
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

#Reading values from over USB from the sensor
ser = serial.Serial('/dev/ttyUSB0')

dataTwoFive = []
dataTen = []

while True:
    # "Try, except" incase of network issues
    try:
        # Reading data from USB
        data = []
        for index in range(0,10):
            datum = ser.read()
            data.append(datum)
         
        # PM2.5 reading
        pmtwofive = int.from_bytes(b''.join(data[2:4]), byteorder='little') / 10
        print("PM2.5:")
        print(pmtwofive)
        # PM10 reading
        pmten = int.from_bytes(b''.join(data[4:6]), byteorder='little') / 10
        print("PM10:")
        print(pmten)
        
        #### Writing to spreadsheet
        values = [[datetime.now().strftime("%d/%m/%Y %H:%M:%S"),pmtwofive, pmten]] #Information to be written to Sheets
        body = {'values':values} # Used if there are more complex structures to be written
        # Uploading the data:
        result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range='AirQuality!A2',
        valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS' , body=body).execute()
                
        
    except:
        print("An exception occurred at {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        
    time.sleep(60) # Take a reading once a minute


