import csv
from math import ceil
import mysql.connector
from mysql.connector import Error


# search csv files for airport info and runway info
def get_runways_info(self):
    airport = self.airport_entry.get()
    if len(airport) != 4 or type(airport) is not str:
        return self.open_errorwindow(message="Invalid airport. Airport must be in ICAO format.")
    runways = {}
    runways_info = {"LENGTH": None, "WIDTH": None, "COMP_CODE": None}
    airport_info = {"X": None, "Y": None, "GLOBAL_ID": None, "NAME": None, "ELEVATION": None, 
                    "SERVCITY": None, "STATE": None, "IDENT": None, "ICAO_ID": None, "Runways": runways}

    # encoding='utf-8-sig' to strip UTF-8 Byte Order Mark
    with open('C:/Users/pbaci/OneDrive/Code/Final-Project/airports.csv', 'r', encoding='utf-8-sig') as airports_file:
        reader = csv.DictReader(airports_file)

        # iterate through csv looking for row with entered airport
        for row in reader:
            if airport == row["ICAO_ID"] or airport == row["IDENT"]:
                for item in airport_info:
                    try:
                        airport_info[item] = row[item]
                    # to handle "Runways" not being assigned
                    except KeyError:
                        continue
        
        # if airport is invalid open error window
        if airport_info["GLOBAL_ID"] == None:
            self.open_errorwindow(message="Invalid airport")

    # set runways_info with info from this csv
    with open('C:/Users/pbaci/OneDrive/Code/Final-Project/runways-filtered.csv', 'r') as runways_file:
        reader = csv.DictReader(runways_file)

        for row in reader:
            if airport_info["GLOBAL_ID"] == row["AIRPORT_ID"]:
                runways_info = {"LENGTH": row["LENGTH"], "WIDTH": row["WIDTH"], "COMP_CODE": row["COMP_CODE"]}
                runways[row["DESIGNATOR"]] = runways_info

        # if no runways are found open error window
        if runways_info["LENGTH"] == None:
            self.open_errorwindow(message="Could not find runways")
    
    runway_list_combined = list(runways.keys())
    runway_list = []
    split_runways = False

    # create new list of individual runways
    for item in runway_list_combined:
        if '/' in item:
            runway_list.extend(item.split('/'))
        elif '-' in item:
            runway_list.extend(item.split('-'))
        else:
            runway_list.append(item)

    # add reciprocal runways if not in runway_list
    for item in runway_list:
        # check if item is a number without a letter, if so add reciprocal
        if item.isdigit():
            number = int(item)
            opposite_number = (number + 18) % 36
            if opposite_number == 0:
                opposite_number = 36

            # add zero in front if it needs it
            if opposite_number < 10:
                opposite_value = str(opposite_number).zfill(2)
            else:
                opposite_value = str(opposite_number)

        else:
            # identify the number and letters in the runway designator
            if len(item) == 3:
                number = int(item[:2])
                letter = item[2]
            elif len(item) == 2:
                number = int(item[:1])
                letter = item[1]

            # get reciprocal number
            opposite_number = (number + 18) % 36
            if opposite_number == 0:
                opposite_number = 36

            # add zero in front if it needs it
            if opposite_number < 10:
                opposite_value = str(opposite_number).zfill(2)
            else:
                opposite_value = str(opposite_number)

            # get and add reciprocal letters
            if letter == 'C':
                opposite_value += 'C'
            elif letter == 'L':
                    opposite_value += 'R'
            elif letter == 'R':
                    opposite_value += 'L'

        # filter duplicates
        if opposite_value not in runway_list:
            runway_list.append(opposite_value)

        # add opposite value to airport info["Runways"]
        try:
            if opposite_value not in runways:
                runways[opposite_value] = runways[item]
        except KeyError:
            split_runways = True
            pass
    
    # split airport_info["Runways"] if necessary
    if split_runways:
        new_runways = {}
        for key, value in runways.items():
            runway_nums = key.split("/")
            for num in runway_nums:
                new_key = num
                new_runways[new_key] = value
        runways = new_runways
        airport_info["Runways"] = runways

    # configure combobox selections and airport information
    self.runway_dropdown.configure(values=runway_list)
    self.airportinfo.configure(text=f"Name:  {airport_info['NAME']}\nLocation:  {airport_info['SERVCITY'].title()}, {airport_info['STATE']}\n
                               Elevation:  {int(round(float(airport_info['ELEVATION'])))}ft")
    self.runway_dropdown.set("Runway")

    return airport_info


# validate integer entries
def validate(self, value, min_value, max_value, message):
    try:
        value = int(value)
    except ValueError:
        return self.open_errorwindow(message=message)

    if not min_value <= value <= max_value:
        return self.open_errorwindow(message=message)

    return value


# query database for distances and interpolate if necessary
def get_distances(to_weight, temp, pa):
    global values
    values = initialize(to_weight, temp, pa)
    to_wt_low_query, to_wt_hi_query, temp_gnd_query, temp_obst_query,  = values[0], values[1], values[2], values[3]
    pa_low_query, pa_hi_query, liftoff_speed, speed_at_fifty = values[4], values[5], values[6], values[7]
    
    # if temperature interpolation is required
    if temp_bool:
        distances = interpolate_temp(to_wt_low_query, temp, pa_low_query)
    else:
        query = f"SELECT {temp_gnd_query}, {temp_obst_query} FROM {to_wt_low_query} WHERE pa = {pa_low_query};"
        d = read_query_all(connection, query)
        distances = [d[0][0], d[0][1]]
    
    # ground roll and obstacle distances are called and updated if different interpolation is required
    gnd_roll, obst = distances[0], distances[1]
    
    # if pressure altitude interpolation is required
    if pa_bool:
        distances = interpolate_pa(to_wt_low_query, temp, pa, pa_hi_query, gnd_roll, obst)
        gnd_roll, obst = distances[0], distances[1]
    
    if wt_bool:
        # repeat checks and queries for higher weight table
        if temp_bool:
            distances = interpolate_temp(to_wt_hi_query, temp, pa_low_query)
        else:
            query = f"SELECT {temp_gnd_query}, {temp_obst_query} FROM {to_wt_hi_query} WHERE pa = {pa_low_query};"
            d = read_query_all(connection, query)
            distances = [d[0][0], d[0][1]]
        
        hi_wt_gnd, hi_wt_obst = distances[0], distances[1]
        
        if pa_bool:
            distances = interpolate_pa(to_wt_hi_query, temp, pa, pa_hi_query, gnd_roll, obst)
            hi_wt_gnd, hi_wt_obst = distances[0], distances[1]
        
        distances = interpolate_weight(to_weight, gnd_roll, obst, hi_wt_gnd, hi_wt_obst)
        gnd_roll, obst = distances[0], distances[1]
        
    return int(gnd_roll), int(obst), liftoff_speed, speed_at_fifty


# initialize variables and determine if interpolation is required for each variable
def initialize(to_weight, temp, pa):
    global wt_bool
    global temp_bool
    global pa_bool
    wt_bool, temp_bool, pa_bool = False, False, False
    to_wt_low_query, to_wt_hi_query, temp_gnd_query, temp_obst_query, low_wt_bound, hi_wt_bound = None, None, None, None, None, None
    
    # if takeoff weight != to a table weight then interpolation required
    # assign table queries to be interpolated
    if 2200 <= to_weight < 2400:
        to_wt_low_query = "to_low"
        to_wt_hi_query = "to_mid"
        liftoff_speed = 48
        speed_at_fifty = 54
        low_wt_bound = 2200
        hi_wt_bound = 2400
        wt_bool = True
    elif 2400 <= to_weight < 2550:
        to_wt_low_query = "to_mid"
        to_wt_hi_query = "to_max"
        liftoff_speed = 51
        speed_at_fifty = 56
        low_wt_bound = 2400
        hi_wt_bound = 2550
        wt_bool = True
    elif to_weight == 2550:
        to_wt_low_query = "to_max"
        liftoff_speed = 48
        speed_at_fifty = 54
    
    # if temperature != to a column then interpolation required
    # assign column queries if interpolation is not required
    if temp <= 0:
        temp_gnd_query = "zeroc_gnd"
        temp_obst_query = "zeroc_obst"
    elif temp == 10:
        temp_gnd_query = "tenc_gnd"
        temp_obst_query = "tenc_obst"
    elif temp == 20:
        temp_gnd_query = "twentyc_gnd"
        temp_obst_query = "twentyc_obst"
    elif temp == 30:
        temp_gnd_query = "thirtyc_gnd"
        temp_obst_query = "thirtyc_obst"
    elif temp == 40:
        temp_gnd_query = "fortyc_gnd"
        temp_obst_query = "fortyc_obst"
    else:
        temp_bool = True
    
    # if temperature != to a column then interpolation required
    if not pa in range(0, 8001, 1000):
        pa_bool = True

    # assign pressure altitude queries to be interpolated
    pa_hi = ceil(pa / 1000) * 1000
    if pa_hi == 0:
        pa_low = 0
    else:
        pa_low = pa_hi - 1000
    pa_low_query, pa_hi_query = str(pa_low), str(pa_hi)
    
    return to_wt_low_query, to_wt_hi_query, temp_gnd_query, temp_obst_query, pa_low_query, pa_hi_query, liftoff_speed, speed_at_fifty, low_wt_bound, hi_wt_bound


def interpolate_temp(to_weight_query, temp, pa_query):
    # select appropriate columns based on weight
    if 0 <= temp < 10:
        temp_gnd_low, temp_obst_low = "zeroc_gnd", "zeroc_obst"
        temp_gnd_hi, temp_obst_hi = "tenc_gnd", "tenc_obst"
    elif 10 <= temp < 20:
        temp_gnd_low, temp_obst_low = "tenc_gnd", "tenc_obst"
        temp_gnd_hi, temp_obst_hi = "twentyc_gnd", "twentyc_obst"
    elif 20 <= temp < 30:
        temp_gnd_low, temp_obst_low = "twentyc_gnd", "twentyc_obst"
        temp_gnd_hi, temp_obst_hi = "thirtyc_gnd", "thirtyc_obst"
    elif 30 <= temp < 40:
        temp_gnd_low, temp_obst_low = "thirtyc_gnd", "thirtyc_obst"
        temp_gnd_hi, temp_obst_hi = "fortyc_gnd", "fortyc_obst"
    elif temp == 40:
        temp_gnd_low, temp_obst_low = "fortyc_gnd", "fortyc_obst"

    # query database        
    query = f"SELECT {temp_gnd_low}, {temp_obst_low}, {temp_gnd_hi}, {temp_obst_hi} FROM {to_weight_query} WHERE pa = {pa_query};"
    distances = read_query_all(connection, query)

    # interpolate temperature differences
    temp_difference = (temp % 10) / 10
    low_temp_gnd, low_temp_obst, high_temp_gnd, high_temp_obst = distances[0][0], distances[0][1], distances[0][2], distances[0][3]
    gnd_roll = low_temp_gnd + ((high_temp_gnd - low_temp_gnd) * temp_difference)
    obst = low_temp_obst + ((high_temp_obst - low_temp_obst) * temp_difference)
    
    return gnd_roll, obst


def interpolate_pa(to_weight_query, temp, pa, pa_hi_query, gnd_roll_low, obst_low):
    # get variables from initialization values
    temp_gnd_query, temp_obst_query = values[2], values[3] 
    
    # if temperature interpolation required preform it for the next pressure altitude column
    if temp_bool:
        distances = interpolate_temp(to_weight_query, temp, pa_hi_query)
    else:
        query = f"SELECT {temp_gnd_query}, {temp_obst_query} FROM {to_weight_query} WHERE pa = {pa_hi_query};"
        d = read_query_all(connection, query)
        distances = [d[0][0], d[0][1]]
        
    gnd_roll_hi, obst_hi = distances[0], distances[1]
    
    # interpolate between pressure altitude differences
    pa_difference = (pa % 1000) / 1000
    gnd_roll = gnd_roll_low + ((gnd_roll_hi - gnd_roll_low) * pa_difference)
    obst = obst_low + ((obst_hi - obst_low) * pa_difference)
    
    return gnd_roll, obst

    
def interpolate_weight(to_weight, low_wt_gnd, low_wt_obst, hi_wt_gnd, hi_wt_obst):
    # define variables from initialization
    low_wt_bound, hi_wt_bound = values[8], values[9]
    
    # interpolate weight
    wt_bound_difference = hi_wt_bound - low_wt_bound
    wt_difference = (to_weight - low_wt_bound) / wt_bound_difference
    gnd_roll = low_wt_gnd + ((hi_wt_gnd - low_wt_gnd) * wt_difference)
    obst = low_wt_obst + ((hi_wt_obst - low_wt_obst) * wt_difference)
    
    return gnd_roll, obst

    
def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
    except Error as err:
        print(f"Error: '{err}'")

    return connection
    
    
def read_query_all(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")
    
        
connection = create_db_connection("localhost", "username", "password", "data")
