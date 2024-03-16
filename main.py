from flask import Flask, jsonify
import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, time
import pandas as pd


app = Flask(__name__)



def get_time_info():
    # Get the current date and time
    current_time = datetime.now()

    # Get the day of the week (0=Monday, 1=Tuesday, ..., 6=Sunday)
    day_of_week = current_time.weekday()

    # Round up the current minute to the nearest half-hour
    rounded_minute = (current_time.minute + 15) // 15 * 15
    if rounded_minute == 60:
        rounded_minute = 0
        current_time += timedelta(hours=1)

    # Round the current time to the nearest quarter-hour
    rounded_time = current_time.replace(minute=rounded_minute, second=0, microsecond=0)

    # Convert the rounded time to decimal representation
    decimal_time = rounded_time.hour + rounded_time.minute / 60


    # Get the name of the day of the week
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = days_of_week[day_of_week]
    # Example timestamp or datetime object
    timestamp = datetime.now()

    # Get the date from the timestamp
    date = timestamp.date()

    return day_name, decimal_time, date

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
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print("CSV file not found. Creating a new DataFrame.")
        df = pd.DataFrame(columns=['date', 'day', 'hour','capacity'])

    df.loc[len(df)] = new_row
    df.to_csv(csv_file, index=False)

    return df

def is_weekday(dt):
    # Monday is 0 and Sunday is 6
    return dt.weekday() < 5

def is_gym_open():
    dt = datetime.now()
    if is_weekday(dt):
        return time(7, 0) <= time(datetime.now().hour,datetime.now().minute) <= time(23, 30)
    else:
        return time(8, 30) <= time(datetime.now().hour,datetime.now().minute) <= time(19, 0) 
        
@app.route('/')
def index():
    try:
        if is_gym_open():
            capacity = get_value()
            assert(capacity)
            day, hour, date = get_time_info()
            new_row = {'date':date, 'day': day, 'hour': hour, 'capacity': capacity}
            load_append_save("data.csv", new_row)
        return jsonify(new_row)
    except:
        return jsonify({"Call failed."})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
