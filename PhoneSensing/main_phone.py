# Joshua Moody for Design Engineering SIoT module
# Janurary 2021

# Imports for writing to spreadsheets
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

#Other imports
import time
from datetime import datetime
from paho.mqtt import client as mqtt_client # For MQTT


print("Running...")


# MQTT setup
broker = 'broker.emqx.io'
port = 1883
topic = "/JM/phone/#"
client_id = 'JoshPi'
 
# Variables setup
xvar = False
yvar = False
zvar = False
noisebool = False
x = 0
y = 0
z = 0
noise = 0



#### Setting up to use Google Sheets API ####

# Scope of permissions required
# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# The ID of the spreadsheet
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


# Connection function for MQTT

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client
    
# Primary function used for publishing with MQTT

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S") # Creating timestamp for the data
        # Collecting one of each piece of data before uploading all at once
        if msg.topic == "/JM/phone/Gyroscope/x":
            print(timestamp)
            print("Number of loops: {}".format(nloops))
            global x
            x = float(msg.payload.decode())
            global xvar
            xvar = True
        elif msg.topic == "/JM/phone/Gyroscope/y":
            global y
            y = float(msg.payload.decode())
            global yvar
            yvar = True
        elif msg.topic == "/JM/phone/Gyroscope/z":
            global z
            z = float(msg.payload.decode())
            global zvar
            zvar = True
        elif msg.topic == "/JM/phone/noise/decibels":
            global noise
            noise = float(msg.payload.decode())
            global noisebool
            noisebool = True
        # if all the data we want has been collected:
        if xvar == True and yvar == True and zvar == True and noisebool == True:
            print("Gyroscope: ({:0.2f},{:0.2f},{:0.2f})".format(x,y,z))
            gyro = (x**2+y**2+z**2)**0.5
            print("Noise level: {:0.2f}".format(noise))
            xvar = False
            yvar = False
            zvar = False
            noisebool = False
            
            # Then upload to the spreadsheet. "Try, except" in case of network problems
            try:
                ### Reading previous values from spreadsheet for moving average ###
                print("Reading spreadsheet values")
                wholespreadsheet = service.spreadsheets()
                sheet2 = wholespreadsheet.values().get(spreadsheetId=spreadsheet_id, range='PhoneSensors!A:F').execute()
                GyroValues = sheet2.get('values', [])
                
                #### Calculating average of current value and previous 4
                sumof5 = gyro
                for i in range(1, 5):
                    sumof5 += float(GyroValues[-i][5])
                average = float(sumof5)/float(5)               
                
                #### Writing to spreadsheet
                print("Writing to spreadsheet")
                values = [[timestamp,noise,x,y,z,gyro,average]] #Information to be written to Sheets
                body = {'values':values} # Used if there are more complex structures to be written
                # Uploading the data:
                result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range='PhoneSensors!A2',
                valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS' , body=body).execute()
                print("Data written at {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                print()
        
            except:
                print("An exception occurred at {0}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                print()


    client.subscribe(topic)
    client.on_message = on_message


# Function which calls other functions in order to make 
# the MQTT connection and then subscribe to the topic
def run():
    print("Connecting MQTT")
    global client
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()

nloops = 0 # for debugging

# Code which runs
while True:
    run() # Make connection, subscribe and then upload data
    time.sleep(60)
    # Connection is cut and restarted every 60s to avoid times where 
    # it has disconnected, reconnected and then not recieved anything
    client.loop_stop()
    nloops += 1 # For debugging
    print("looping")




