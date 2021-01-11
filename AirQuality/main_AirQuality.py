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
        ser.flushInput()
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
        # Current time
        timeofreadings = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        
        # Reading from spreadsheet to calculate weighted moving average
        
        # Fetch previous values
        wholespreadsheet = service.spreadsheets()
        sheet1 = wholespreadsheet.values().get(spreadsheetId=spreadsheet_id, range='AirQuality!B2:C').execute()
        airqualitydata = sheet1.get('values',[])
        

        # Calculate weighted moving average with 9 previous values
        pm25data = [float(i[0]) for i in airqualitydata]
        pm10data = [float(i[1]) for i in airqualitydata]
        pm25av = pmtwofive*0.2 + 0.1*(pm25data[-1]+pm25data[-2]+pm25data[-3]+pm25data[-4]+pm25data[-5]+pm25data[-6]+pm25data[-7])+0.05*(pm25data[-8]+0.05*pm25data[-9])
        pm10av = pmten*0.2 + 0.1*(pm10data[-1]+pm10data[-2]+pm10data[-3]+pm10data[-4]+pm10data[-5]+pm10data[-6]+pm10data[-7])+0.05*(pm10data[-8]+0.05*pm10data[-9])

        
        
        

        #### Writing to spreadsheet
        values = [[timeofreadings,pmtwofive, pmten, pm25av, pm10av]] #Information to be written to Sheets
        body = {'values':values} # Used if there are more complex structures to be written
        # Uploading the data:
        result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range='AirQuality!A2',
        valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS' , body=body).execute()
        print("Data written at {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        print()
        
    except:
        print("An exception occurred at {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        
    time.sleep(60) # Take a reading roughly once a minute


