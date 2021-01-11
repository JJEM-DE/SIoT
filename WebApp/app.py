# Joshua Moody for Design Engineering SIoT module
# January 2021


# Imports for writing to spreadsheets
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Other imports
from flask import Flask, render_template, request # Import for web app
from datetime import datetime
import numpy as np


# Setting up spreadsheet access
print("Setting up spreadsheet access")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets'] # Scope of permissions required
spreadsheet_id = '1A24Y1SYIFnIcBoFuPChf3bq4sZSUGBj5PF7Pp4J_ETQ' # The ID of the spreadsheet
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




# Setting up web app using flask

app = Flask(__name__)


print("Running app")

@app.route('/')
def index():
	#Read the spreadsheet
	print("Accessing the spreadsheet")
	sheet = service.spreadsheets()


	### Get and manipulate air quality data ###

	sheet1 = sheet.values().get(spreadsheetId=spreadsheet_id, range='AirQuality!A2:E').execute()
	values1 = sheet1.get('values', [])
	#Seperate the columns of data
	time = [i[0] for i in values1]
	pm25 = [i[3] for i in values1] #Moving average value
	pm10 = [i[4] for i in values1] #Moving average value
	#Convert date string to useful datetime and "seconds since epoch" arrays
	newtime = np.empty(len(time), dtype=object)
	seconds = np.empty(len(time), dtype=object)
	for i in range(len(time)):
		newtime[i] = datetime.strptime(time[i], "%d/%m/%Y %H:%M:%S")
		seconds[i] = newtime[i].timestamp()*1000 # Highcharts requires time in miliseconds
	#Convert to numpy array so strings can be converted to floats
	pm25 = np.array(pm25).astype(np.float)
	pm10 = np.array(pm10).astype(np.float)
	# Create arrays ready to be plotted by highcharts in js
	pm25t = []
	pm10t = []
	for i in range(len(seconds)):
		pm25t.append([seconds[i], pm25[i]])
		pm10t.append([seconds[i], pm10[i]])
	# Downsampling the air quality data
	pm25tshort = []
	pm10tshort = []
	for i in range(len(seconds)):
		if i%1 == 0: #was 4
			pm25tshort.append(pm25t[i])
			pm10tshort.append(pm10t[i])



	### Get and manipulate gyroscope data ###

	sheet2 = sheet.values().get(spreadsheetId=spreadsheet_id, range='PhoneSensors!A83523:C').execute()
	values2 = sheet2.get('values', [])
	#Seperate the columns of data
	time2 = [i[0] for i in values2] # timestamps
	gyro  = [i[1] for i in values2] # Magnitude of gyroscope readings
	gyroAv= [i[2] for i in values2] # Moving average of gyroscope magnitudes
	#Convert date string to useful datetime and "seconds since epoch" arrays
	newtime2 = np.empty(len(time2), dtype=object)
	seconds2 = np.empty(len(time2), dtype=object)
	for i in range(len(time2)):
		newtime2[i] = datetime.strptime(time2[i], "%d/%m/%Y %H:%M:%S")
		seconds2[i] = newtime2[i].timestamp()*1000 # Highcharts requires time in miliseconds
	#Convert to numpy array so strings can be converted to floats
	gyro  = np.array(gyro).astype(np.float)
	gyroAv = np.array(gyroAv).astype(np.float)
	# Create arrays ready to be plotted by highcharts in javascript
	gyrot = []
	gyroAvt = []
	for i in range(len(seconds2)):
		gyrot.append([seconds2[i], gyro[i]])
		gyroAvt.append([seconds2[i], gyroAv[i]])


	### Take gyroAvt and identify activites ###

	# Initialising variables
	stationary = []
	smallMove = []
	bigMove = []
	currentActivity = "None"
	first = True # Avoid errors on first loop when there's no previous data
	print("Starting loop")
	# Creates arrays with pairs of timestamps indicating when an action starts and ends
	for previous, datapoint in zip(gyroAvt, gyroAvt[1:]): # For each moving average value, and the one preceeding it:
		if first == False and (datapoint[0]-previous[0]) < 60000: # If there isn't a jump in the readings of more than 60s
			if datapoint[1] < 0.025: # If there's negligible movement
				if currentActivity != "Stationary":
					stationary.append([previous[0], datapoint[0]])
					currentActivity = "Stationary"
				else:
					stationary[-1][1] = datapoint[0]
			elif datapoint[1] < 1: # If there's a small movement
				if currentActivity != "Small Move":
					smallMove.append([previous[0], datapoint[0]])
					currentActivity = "Small Move"
				else:
					smallMove[-1][1] = datapoint[0]
			else: # If there's a large movement
				if currentActivity != "Big Move":
					bigMove.append([previous[0], datapoint[0]])
					currentActivity = "Big Move"
				else:
					bigMove[-1][1] = datapoint[0]
		else:
			currentActivity = "None"
		first = False

	# Remove small sections of stationary which generally correspond to smallMove
	for pair in stationary:
		if pair[1] - pair [0] <= 20000:
			stationary.remove(pair)
			smallMove.append(pair)


	return render_template('index.html', data = [pm25tshort, pm10tshort, gyrot, stationary, smallMove, bigMove]) # "data" gets passed to the html file



# Running the app

if __name__ == '__main__':
	app.debug = True
	app.run()
