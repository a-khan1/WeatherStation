import requests
import config
import pygsheets
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import os

#find number of rows in a sheet
def numberOfRows(worksheet):
    rows = worksheet.get_col(2)
    length = len(rows)
    if rows[0] == '':
        return 1
    for i in range(1,length):
        if(rows[i] == ''):  
            return i
    return 0


#open spreadsheet
gc = pygsheets.authorize(outh_file=config.outh_file,credentials_directory = config.credentials_directory)
sh = gc.open('sensor readings')
sheets = sh.worksheets()

# Convert the start and end times to ISO 8601 format with the Pacific Time Zone offset
# need to check last row of last worksheet to see where to continue data
lastSheet = sheets[-1]
num_rows = numberOfRows(lastSheet)
date_string1 = lastSheet.get_row(num_rows)[0]
date_string2 = str(datetime.now())

# Parse the dates into datetime objects
dt1 = datetime.fromisoformat(date_string1)
dt2 = datetime.fromisoformat(date_string2)

# Convert the datetime objects to UTC
dt1_utc = dt1.astimezone(tz=None).replace(tzinfo=None)
dt2_utc = dt2.astimezone(tz=None).replace(tzinfo=None)

# Format the datetime objects in ISO 8601 format with the UTC time zone
START_TIME = dt1_utc.isoformat() + '-08:00'
END_TIME = dt2_utc.isoformat() + '-08:00'
TIME_ZONE = 'America/Los_Angeles'
API_KEY = config.api_key
CHANNEL_ID = config.channel_id

response=requests.get(f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={API_KEY}&start={START_TIME}&end={END_TIME}&timezone={TIME_ZONE}")
print(response)
values = response.json()
#convert readings to dataframe
readings = {'DATE':[],'temperature':[],'humidity':[]}
numValues = values['channel']['last_entry_id']
print(numValues)
print(num_rows)

for i in range(len(values['feeds'])):
    readings['DATE'].append(values['feeds'][i]['created_at'])
    readings['temperature'].append(values['feeds'][i]['field1'])
    readings['humidity'].append(values['feeds'][i]['field2'])
df = pd.DataFrame(data=readings)

#create new worksheet to add data to
worksheetTitle = dt1.strftime('%Y-%m-%d@%H:%M:%S') + " to " + dt2.strftime('%Y-%m-%d@%H:%M:%S')
wks = sh.add_worksheet(str(worksheetTitle),6000,2)

#use dataframe to update google sheet
wks.set_dataframe(df,(1,1))

#convert readings to np array to be used in plots
temperatures = np.array(readings['temperature'])
temperatures = temperatures[temperatures != None]
temperatures = temperatures.astype(float)

humidities = np.array(readings['humidity'])
humidities = humidities[humidities != None]
humidities = humidities.astype(float)

dates = [datetime.fromisoformat(date) for date in readings['DATE']]

# Initialize plot
figure, axis = plt.subplots(2,sharex=True)
  
# plot temperatures
axis[0].plot_date(dates, temperatures, fmt='-b')
axis[0].set_title("temperatures")
axis[0].set(xlabel='time',ylabel='Degrees Celsius')
  
# plot humidities
axis[1].plot_date(dates, humidities,fmt='-g')
axis[1].set_title("humidities")
axis[1].set(xlabel='time',ylabel='Humidity %')

for i in range(len(axis)):
    axis[i].xaxis_date()
# formatting x axis
figure.autofmt_xdate()

#plot spacing
figure.subplots_adjust(hspace=0.5)

#save image of plot to be used elsewhere
plt.savefig(config.image_save_directory)

#TO DO
#scale horizontal to date || proly D
#save image to same directory as flask || D
#automate script using some scheduler || last
#ensure all data is in sheets and no overlap of data || probably done