import copy
import csv
from bs4 import BeautifulSoup
import requests
import uuid
from flask import Flask, jsonify, request, render_template, session, url_for, flash, redirect
from flask_restful import Resource, Api
from datetime import datetime, timedelta
import json
import collections
collections.MutableSequence = collections.abc.MutableSequence
collections.Iterable = collections.abc.Iterable
from flask_navigation import Navigation
import pyodbc
import math
import sys
# Create the Flask app
app = Flask(__name__)

# Create an API object
api = Api(app)

nav = Navigation(app)
#Change the endpoints
nav.Bar('top', [
    nav.Item('Home','homePage'),
    nav.Item('Housing', 'display_hotel_page'),
    nav.Item('Activities', 'event_finder'),
    nav.Item('Travel','travelPage')
])

app.secret_key = 'Icannottellyou'

@app.before_request
def set_session_token():
    if 'user_token' not in session:
        session['user_token'] = str(uuid.uuid4())  # Generate a unique ID for the user

#Takes in the orgin airport, destination airport (Both need to me in MIA, JFK format), fly out data, fly back dat (Both dates need to be in YYYY-MM-DD), number of people
#Returns information of when the flights leave and get back, # of flights, price, total time of travel, airport  codes of each one you go through, price and flight score (indecating if its good or not)
def get_flight(orgin,destination,start_date,end_date,people):
    
    if(session['flight_data']==None):
        
        

        api_key = 'thisisasecret'
        


        #https://api.flightapi.io/roundtrip/<api-key>/<departure_airport_code>/<arrival_airport_code>/<departure_date>/<arrival_date>/<number_of_adults>/<number_of_childrens>/<number_of_infants>/<cabin_class>/<currency>
        response = requests.get(f"https://api.flightapi.io/roundtrip/{api_key}/{orgin}/{destination}/{start_date}/{end_date}/{people}/0/0/Economy/USD")
        if response.status_code != 200:
            return {"error": f"Failed to fetch data: {response.status_code} - {response.text}"}
        data = response.json()
        file_name = 'checkforflights.json'
        with open(file_name, 'w') as file:
            json_data = json.dumps(data, indent=4)
            file.write(json_data)
        
        starting_data = data['itineraries']
        

        if len(starting_data) == 0:
            response = requests.get(f"https://api.flightapi.io/roundtrip/{api_key}/{orgin}/{destination}/{start_date}/{end_date}/{people}/0/0/Economy/USD")
            if response.status_code != 200:
                return {"error": f"Failed to fetch data: {response.status_code} - {response.text}"}
            data = response.json()
            file_name = 'checkforflights.json'
        
        starting_data = data['itineraries']

        airport_codes_decypher = {}
        agent_codes_decypher = {}
        agent_codes_list = []
        #Finding the codes to there given aiports
        for x in range(0,len(data['places'])):
            airport_codes_decypher[str(data['places'][x]['id'])]= data['places'][x]['display_code']
        for x in range(0,len(data['carriers'])):
            agent_codes_decypher[data['carriers'][x]['id']] = data['carriers'][x]['name']
            agent_codes_list.append(agent_codes_decypher[data['carriers'][x]['id']])
        
        session['agent_codes'] = agent_codes_list
    
        flight_info = []

        for x in range(0,len(starting_data)):
            airport_list_codes = []
            for i in range(0,len(starting_data[x]['pricing_options'][0]['items'][0]['fares'])):
                airport_code = starting_data[x]['pricing_options'][0]['items'][0]['fares'][i]['segment_id'].split('-')[0]

                airport_list_codes.append(airport_codes_decypher[airport_code])
            
            #print("Flight: ",x," ",starting_data[x])
            leg1_start_time = starting_data[x]["leg_ids"][0].split('-')[1] #ID for first leg of trip
            leg1_end_time = starting_data[x]["leg_ids"][0].split('-')[6] #ID for first leg of trip
            leg2_start_time = starting_data[x]["leg_ids"][1].split('-')[1] #ID for second leg of trip
            leg2_end_time = starting_data[x]["leg_ids"][1].split('-')[6] #ID for first leg of trip
            airline_code = starting_data[x]["leg_ids"][0].split('-')[3]
            airline_code = "-"+airline_code
            airline_code = int(airline_code)

            leg1_start_time_format = datetime.strptime(leg1_start_time, "%y%m%d%H%M")
            leg1_end_time_format = datetime.strptime(leg1_end_time, "%y%m%d%H%M")  
            leg1_time_diffrence = leg1_end_time_format - leg1_start_time_format


            leg2_start_time_format = datetime.strptime(leg2_start_time, "%y%m%d%H%M")
            leg2_end_time_format = datetime.strptime(leg2_end_time, "%y%m%d%H%M")  
            leg2_time_diffrence = leg2_end_time_format - leg2_start_time_format
        
            

            temp_info = {
                "Travel_out_start_time": leg1_start_time_format.strftime("%B %d, %Y at %I:%M %p"),
                "Travel_out_end_time": leg1_end_time_format.strftime("%B %d, %Y at %I:%M %p"),
                "Travel_back_start_time": leg2_start_time_format.strftime("%B %d, %Y at %I:%M %p"),
                "Travel_back_end_time": leg2_end_time_format.strftime("%B %d, %Y at %I:%M %p"),
                "Number_total_flights": len(starting_data[x]['pricing_options'][0]['items'][0]['segment_ids']), #total number of flights 
                "Price": starting_data[x]['pricing_options'][0]['price']['amount'],
                "Travel_out_time": leg1_time_diffrence,
                "Travel_back_time": leg2_time_diffrence,
                "Total_travel":  leg1_time_diffrence + leg2_time_diffrence,
                "airport_codes": airport_list_codes,
                "Price_Score": starting_data[x]['score'],
                'flight_score': starting_data[x]['pricing_options'][0]['score'],
                'Airline': agent_codes_decypher[airline_code]
                }
            flight_info.append(temp_info)
        '''
        if len(flight_info) == 0:
            return "No flight data found"
        '''

        copy_flight_info = copy.deepcopy(flight_info)
        for x in range(0,len(copy_flight_info)):
                copy_flight_info[x]['Travel_out_start_time'] = str(copy_flight_info[x]['Travel_out_start_time'])
                copy_flight_info[x]['Travel_out_end_time'] = str(copy_flight_info[x]['Travel_out_end_time'])
                copy_flight_info[x]['Travel_back_start_time'] = str(copy_flight_info[x]['Travel_back_start_time'])
                copy_flight_info[x]['Travel_back_end_time'] = str(copy_flight_info[x]['Travel_back_end_time'])
                copy_flight_info[x]['Travel_out_time'] = str(copy_flight_info[x]['Travel_out_time'])
                copy_flight_info[x]['Travel_back_time'] = str(copy_flight_info[x]['Travel_back_time'])
                copy_flight_info[x]['Total_travel'] = str(copy_flight_info[x]['Travel_back_time'])

    
        if 'user_id' in session:
            user_id = session['user_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO TravelDetails (UserID, TravelInfo) VALUES (?, ?)", (user_id, json.dumps(copy_flight_info)))
            conn.commit()
            conn.close()
            
            
            session['flight_data'] ="full"
        else:
            print("Flight_not_stored")
        
        sorted_data_travel_and_price = sorted(
        flight_info,
        key=lambda x: (x['Price'], x['Total_travel'])
        ) 

        return sorted_data_travel_and_price[:3], agent_codes_list
    
    else:

        if 'user_id' in session:
            user_id = session['user_id']

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 TravelInfo FROM TravelDetails WHERE UserID = ? ORDER BY TravelID DESC;", (user_id,))
            most_recent_travel_info = cursor.fetchone()
            conn.close()
            list_please = list(most_recent_travel_info)  # Converts the pyodbc.Row to a dictionary

            # Now you can convert the dictionary to JSON
            
            # Step 1: Extract the string
            json_string = list_please[0]  # Get the first element of the list

            # Step 2: Parse the JSON string
            try:
                parsed_data = json.loads(json_string)  # Convert JSON string to Python object
                
            except json.JSONDecodeError as e:
                print("Error parsing JSON:", e)


        else:
            flash('You need to log in to view your recent flights.', 'error')
            return redirect(url_for('login'))

        
        
        copy_flight_info = parsed_data

    # Assuming copy_flight_info is your data list
        for x in range(len(copy_flight_info)):
            # Convert strings back to datetime objects
            copy_flight_info[x]['Travel_out_start_time'] = datetime.strptime(copy_flight_info[x]['Travel_out_start_time'], '%B %d, %Y at %I:%M %p')
            copy_flight_info[x]['Travel_out_end_time'] = datetime.strptime(copy_flight_info[x]['Travel_out_end_time'], '%B %d, %Y at %I:%M %p')
            copy_flight_info[x]['Travel_back_start_time'] = datetime.strptime(copy_flight_info[x]['Travel_back_start_time'], '%B %d, %Y at %I:%M %p')
            copy_flight_info[x]['Travel_back_end_time'] = datetime.strptime(copy_flight_info[x]['Travel_back_end_time'], '%B %d, %Y at %I:%M %p')

            # Convert strings back to timedelta objects
            copy_flight_info[x]['Travel_out_time'] = timedelta(seconds=time_to_seconds(copy_flight_info[x]['Travel_out_time']))
            copy_flight_info[x]['Travel_back_time'] = timedelta(seconds=time_to_seconds(copy_flight_info[x]['Travel_back_time']))
            copy_flight_info[x]['Total_travel'] = timedelta(seconds=time_to_seconds(copy_flight_info[x]['Total_travel']))
        


        TIME_OF_DAY_RANGES = {
        "morning": (5, 11),      # 5:00 AM - 11:00 AM
        "afternoon": (11, 17),   # 11:00 PM - 5:00 PM
        "evening": (17, 23),     # 5:00 PM - 11:00 PM
        "night": (23, 5),        # 11:00 PM - 5:00 AM (overnight)
        }
        sort_cost = request.form.get('sort_cost', 'na')
        total_time = request.form.get('total_time', 'na')
        airline = request.form.get('airline', 'all')
        time_of_day = request.form.get('time_of_day', 'na')
        direct = request.form.get('direct', 'na')

        
        # Check if any filter is applied, if not, return data as usual
        if sort_cost == 'na' and total_time == 'na' and airline == 'all' and time_of_day == 'na' and direct == 'na':
            # No filters applied, return the data as normal
            sorted_data_travel_and_price = sorted(
                copy_flight_info,
                key=lambda x: (x['Price'], x['Total_travel'])
            )
           
            return sorted_data_travel_and_price[:3],session['agent_codes']
        
        flights = []

        if time_of_day != 'na' and time_of_day in TIME_OF_DAY_RANGES:
                start_hour, end_hour = TIME_OF_DAY_RANGES[time_of_day]
                if start_hour < end_hour:  # Regular time frame (e.g., morning)
                    flights = [
                        flight for flight in copy_flight_info
                        if start_hour <= flight['Travel_out_start_time'].hour < end_hour
                    ]
                    
                else:  # Overnight time frame (e.g., night)
                    flights = [
                        flight for flight in copy_flight_info
                        if flight['Travel_out_start_time'].hour >= start_hour or flight['Travel_out_start_time'].hour < end_hour
                    ]
        else:
            flights = copy.deepcopy(copy_flight_info)  # Use all flight info if no time filter is applied

        if(len(flights)==0 and time_of_day != 'na'):

            alet_message = "No flights in the "+time_of_day
            print(alet_message)

        if airline != 'all':
            flights = [flight for flight in flights if flight['Airline'] == airline]

        if direct != 'na':
            is_direct = direct == 'yes'
            flights = [flight for flight in flights if flight['Number_total_flights'] == 2]

        

        sort_criteria = []
        if sort_cost != 'na':
            reverse_cost = sort_cost == 'high'
            sort_criteria.append(('Price', reverse_cost))

        if total_time != 'na':
            reverse_time = total_time == 'high'
            sort_criteria.append(('Total_travel', reverse_time))

        # Apply sorting by multiple criteria
        for criteria, reverse in reversed(sort_criteria):  # Reversed to prioritize first
            flights = sorted(flights, key=lambda x: x[criteria], reverse=reverse)
        
        for x in range(len(flights)):
            copy_flight_info[x]['Travel_out_start_time'] = copy_flight_info[x]['Travel_out_start_time'].strftime("%B %d, %Y at %I:%M %p")
            copy_flight_info[x]['Travel_out_end_time'] = copy_flight_info[x]['Travel_out_end_time'].strftime("%B %d, %Y at %I:%M %p")
            copy_flight_info[x]['Travel_back_start_time'] = copy_flight_info[x]['Travel_back_start_time'].strftime("%B %d, %Y at %I:%M %p")
            copy_flight_info[x]['Travel_back_end_time'] = copy_flight_info[x]['Travel_back_end_time'].strftime("%B %d, %Y at %I:%M %p")

        return flights[:3],session['agent_codes']
    

def time_to_seconds(time_str):

#Converts a time string (e.g., '1 day, 3:45:00' or '3:45:00') to total seconds.
    try:
        if 'day' in time_str:  # Handle '1 day, 3:45:00'
            days, time_part = time_str.split(', ')
            days = int(days.split()[0])  # Extract the number of days
            hours, minutes, seconds = map(int, time_part.split(':'))
            total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
        else:  # Handle '3:45:00'
            hours, minutes, seconds = map(int, time_str.split(':'))
            total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    except Exception as e:
        print(f"Error parsing time string '{time_str}': {e}")
        raise

def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER='
        'SERVER=;'
        'DATABASE=;'
        'UID=;'
        'PWD='
    )
    return conn


def get_car(start,destination):
    api_key= "nicetry"

    orgin_data = get_geocode(start)
    orgin_lat = orgin_data['Lat']
    orgin_lng = orgin_data['Lng']
    
    destination_data = get_geocode(destination)
    dest_lat = destination_data['Lat']
    dest_lng = destination_data['Lng']

 
  
    #GEt the distance
    response = requests.get(f"https://router.hereapi.com/v8/routes?transportMode=car&origin={orgin_lat},{orgin_lng}&destination={dest_lat},{dest_lng}&return=summary&apiKey={api_key}")
    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.status_code} - {response.text}"}
    clean_data = response.json()


    time = clean_data['routes'][0]['sections'][0]['summary']['duration']
    distnace = clean_data['routes'][0]['sections'][0]['summary']['length']
    distance = distnace/1609.344
    time = (time/60)/60
    data = {
    'Distance': round(distance, 1),
    'Time': round(time, 1)
    }
    return data

def activity_finder(search_location, country):
       
    with open('location_data2.json', 'r') as file:
        data = json.load(file)
    
    if search_location.lower() in data:
        activities = data[search_location.lower()]
    else:
        activities = ["Location Not Found"]

    file.close()
    return activities


#user_input = input("Where do you want to go (city state_abbreviation)? ")
#normally it is just city and state abbreviation, occassionally it is full state name
#https://www.busytourist.com/things-to-do-in-boca-raton-fl/
#https://www.busytourist.com/things-to-do-in-des-moines-iowa/
#https://www.busytourist.com/fun-things-to-do-in-chicago-il/

######################################################################################################

#outside the US
#search_for = "maldives"


def get_geocode(location):
    api_key= "hmmm...WhichAPIkey_Ididn't see one here"
    response = requests.get(f"https://geocode.search.hereapi.com/v1/geocode?q={location}&apiKey={api_key}")
    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.status_code} - {response.text}"}
    clean_data = response.json()
    info = {
        "Lat": clean_data['items'][0]['position']['lat'],
        "Lng": clean_data['items'][0]['position']['lng'],
        "country": clean_data['items'][0]['address']['countryName']
    }
    return info

###new hotel section

# Function to get city ID from MakCorps Mapping API
def get_city_id_from_mapping(city_name):
    url = "https://api.makcorps.com/mapping"
    params = {
        'api_key': 'NotHereEither',  # Replace with your actual API key
        'name': city_name
    }

    # Send the GET request to the MakCorps Mapping API
    response = requests.get(url, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        try:
            json_data = response.json()

            # Check if the response is a list and contains items
            if isinstance(json_data, list) and json_data:
                # Extract the city ID from the first item in the list (assuming the list contains city objects)
                city_id = json_data[0].get('document_id', None)
                return city_id
            else:
                print("No valid city data found.")
                return None
        except ValueError as e:
            print(f"Error parsing response as JSON: {e}")
            return None
    else:
        # Handle any errors that occur with the API request
        print(f"API Error: {response.status_code}, {response.text}")
        return None

# Function to get city data from MakCorps CitySearch API
def get_city_data_from_citysearch(params):
    url = "https://api.makcorps.com/city"

    # Send the GET request to the MakCorps CitySearch API
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Error: {response.status_code}, {response.text}"}


###end new section

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO UserLogins (Username, Password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash('Signup successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except pyodbc.IntegrityError:
            flash('Username already exists. Please choose a different one.', 'error')
        finally:
            conn.close()

    return render_template('signup.html')




@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM UserLogins WHERE Username = ? AND Password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('homePage'))
        else:
            return "Invalid username or password. Please try again."

    return render_template('login.html')

@app.route("/info")
def homePage():
	return render_template('vacation-data.html')

@app.route("/travel",methods=["POST","GET"])
def travelPage():
    # Replace with actual function calls and inputs
    origin = session.get("origin")
    destination = session.get("destination")
    start_date = session.get("start_date")
    end_date = session.get("end_date")
    try:
     num_people = int(session.get("num_people"))
    except (ValueError, TypeError):
        num_people = 1  # Default value or handle error
   

    origin_airport = session.get('origin_airport')
    destination_airport = session.get('destination_airport')


    flights, airlines = get_flight(origin_airport, destination_airport, start_date, end_date, num_people)
    try:
        car_data = get_car(origin, destination)
    except:
        car_data={
            'Distance': 0,
            'Time': 0
        }
    return render_template("travel.html",  flights=flights, car_data = car_data, airlines = airlines)

@app.route('/submit', methods=['POST'])
def submit():
    # Store form data in session
    
    session['origin'] = request.form.get('starting_location')
    session['destination'] = request.form.get('destination')
    session['start_date'] = request.form.get('start_date')
    session['end_date'] = request.form.get('end_date')
    try:
        session['num_people'] = request.form.get('num_people')
    except (ValueError, TypeError):
        session['num_people'] = 1  # Default value or handle error
    
    session['origin_airport'] = request.form.get('airport_out')
    session['destination_airport'] = request.form.get('airport_in')
    session['flight_data'] = None

    return render_template("submit.html")


@app.route("/Events", methods=['GET', 'POST'])
def event_finder():
    location = None
    
    location = session.get("destination")
    location = location.replace(",", "")
    
    
    country = get_geocode(location)
    country = country["country"]
    result = activity_finder(location, country)
    
    if country == "United States":
        with open('location_data5.json', 'r') as file:
            data = json.load(file)
        if location in data:
            image_list = data[location][0]

        return render_template("events.html", search_result=result, location=location, us = True, image_list = image_list)
    
    
    return render_template("events.html", search_result=result, location=location, us = False)

###hotel call
#@app.route('/Hotel', methods=['GET'])
"""def display_hotel_page():
    city_name = request.args.get('city')
    rooms = request.args.get('rooms', '1')
    adults = request.args.get('adults', '1')
    children = request.args.get('children', '0')
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')

    return render_template("hotel.html")"""

@app.route('/Hotel_submit', methods=['GET'])
def display_hotel_page():
    
    city_name = session.get("destination")

    city_id = get_city_id_from_mapping(city_name)
    
    checkin = session.get("start_date")
    checkout = session.get("end_date")
    adults = session.get("num_people")
    rooms = math.ceil(int(adults) / 4)
    
    # Prepare parameters for the CitySearch API
    citysearch_params = {
        'api_key': 'Nope',
        'cityid': city_id, #607603
        'pagination': '0',
        'cur': 'USD',
        'rooms': rooms,
        'adults': adults,
        'checkin': checkin,
        'checkout': checkout
    }

    return_json = get_city_data_from_citysearch(citysearch_params)

    if len(return_json) >= 3:
        return_json = return_json[:3]
    
    print("Return,Json", return_json, file=sys.stdout)
    sorted_list = []
    for i in return_json:
        necessary_info = {}
        necessary_info["name"] = i["name"]
        necessary_info["price"] = i["price1"]
        necessary_info["rating"] = i["reviews"]["rating"]
        necessary_info["vendor"] = i["vendor1"]
        sorted_list.append(necessary_info)

    return render_template("hotel_submit.html", city_data = sorted_list)

#idk if I have to add the resources to this
if __name__ == '__main__':
    app.run(debug=True)