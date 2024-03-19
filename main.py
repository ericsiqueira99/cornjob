import io
from flask import Flask, jsonify
import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, time
import pandas as pd
import pytz

app = Flask(__name__)



def get_time_info():
    # Get the current date and time
    frankfurt_timezone = pytz.timezone('Europe/Berlin')
    current_time = datetime.now(frankfurt_timezone)
    # Get the day of the week (0=Monday, 1=Tuesday, ..., 6=Sunday)
    day_of_week = current_time.weekday()
    # Get the name of the day of the week
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = days_of_week[day_of_week]
    # Example timestamp or datetime object
    timestamp = datetime.now()

    # Get the date from the timestamp
    date = timestamp.date()

    return day_name, current_time.strftime("%H:%M"), date

def get_value():
    # URL of the webpage you want to retrieve
    url = 'https://my.sport.uni-goettingen.de/fiz/'

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the webpage using Beautiful Soup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the tag with the specific ID
        specific_id_tag = soup.find(id='fizgauge')

        if specific_id_tag:
            text = specific_id_tag.find("script").get_text("gauge.set")
            val = re.findall(r'\((.*?)\)', text.split("gauge.set")[-1])[0]
            val = float('%.3f'%(float(val)))
            return val
        else:
            pass
    else:
        return None

def load_append_save(csv_file, new_row):
    file = get_webdav_file_content("gym_capacity.csv")
    df = pd.read_csv(io.StringIO(file.decode('utf-8')))
    df.loc[len(df)] = new_row
    csv_string = df.to_csv(index=False)
    csv_bytes = csv_string.encode('utf-8')
    # Temporary file name
    temp_file_name = csv_file

    # Construct headers with authentication
    headers = {
        'Content-Type': 'text/csv',
    }
    auth = (username, password)

    # Write CSV bytes to a temporary file
    with open(temp_file_name, 'wb') as temp_file:
        temp_file.write(csv_bytes)
    response = requests.put(webdav_url + temp_file_name, data=open(temp_file_name, 'rb'), headers=headers, auth=auth)
    return response.status_code == 201

def is_weekday(dt):
    # Monday is 0 and Sunday is 6
    return dt.weekday() < 5

def is_gym_open():
    frankfurt_timezone = pytz.timezone('Europe/Berlin')
    dt = datetime.now(frankfurt_timezone)
    if is_weekday(dt):
        return time(7, 0) <= time(datetime.now().hour,datetime.now().minute) <= time(23, 30)
    else:
        return time(8, 30) <= time(datetime.now().hour,datetime.now().minute) <= time(19, 0) 

# Replace these variables with your own ownCloud server details
owncloud_url = "https://owncloud.gwdg.de"
username = os.getenv("WEBDAV_USERNAME")
password = os.getenv("WEBDAV_PASS")
subfolder = '/MyData/'
# Set up the WebDAV URL for accessing files
webdav_url = f"{owncloud_url}/remote.php/dav/files/{username}/{subfolder}"

# Authenticate using HTTP Basic Auth
auth = requests.auth.HTTPBasicAuth(username, password)

# Example: Download a file from ownCloud
def get_webdav_file_content(file_name):
    response = requests.get(f"{webdav_url}{file_name}", auth=auth)
    if response.status_code == 200:  # OK
        return response.content
    else:
        print(f"Error: {response.status_code} - {response.text}")


@app.route('/')
def index():
    try:
        if is_gym_open():
            capacity = get_value()
            assert(capacity)
            day, hour, date = get_time_info()
            new_row = {'date':date, 'day': day, 'hour': hour, 'capacity': capacity}
            result = load_append_save("gym_capacity.csv", new_row)
            if result:
                return jsonify(new_row), 200
            else:
                return jsonify({"Error":"Unknown Eror"}), 428
        else:
            return jsonify({"Result":"Gym is closed."}), 428
    except Exception as e:
        return jsonify({"Error":"Unknown Eror"}), 428


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
