from math import cos, ceil
import urllib.request
from utilites import validate, get_distances
import xml.etree.ElementTree as et


def calculate(self, airport_info, mode):
    if mode == "MANUAL":
        # get entries and validate inputs
        to_weight = validate(self, self.entry1.get(), 1500, 2550, "Takeoff weight must be a number between 1500 and 2550")
        temp_c = validate(self, self.entry2.get(), -20, 40, "Temperature must be a number between -20 and 40")
        wind_dir = validate(self, self.entry3.get(), 1, 360, "Wind direction must be a number between 001 and 360")
        wind_speed = validate(self, self.entry4.get(), 0, 50, "Wind speed must be a number between 0 and 50")
        elevation = validate(self, self.entry5.get(), -500, 8000, "Airport elevation must be a number between -500 and 8000")
        runway_heading = validate(self, self.entry6.get(), 1, 360, "Runway heading must be a number between 001 and 360")

        # if error is thrown stop calculating
        try:
            if self.error_window.winfo_exists():
                return
        except AttributeError:
            pass
        
        # validate altimiter entry
        altimeter = self.entry7.get()
        try:
            altimeter = float(altimeter)
        except ValueError:
            return self.open_errorwindow(message="Altimiter must be a number between 28.00 and 31.00")
        if not 28.00 <= altimeter <= 31.00:
            return self.open_errorwindow(message="Altimiter must be a number between 28.00 and 31.00")
        
        # validate surface entry
        surface = self.combobox.get()
        if surface == "Runway Surface":
            return self.open_errorwindow(message="Must select runway surface type")
        
    elif mode == "AUTO":
        to_weight = validate(self, self.weight_entry.get(), 1500, 2550, "Takeoff weight must be a number between 1500 and 2550")

        # if error is thrown stop calculating
        try:
            if self.error_window.winfo_exists():
                return
        except AttributeError:
            pass

        # airport validated in get_runways_info
        airport = self.airport_entry.get()
        runway = self.runway_dropdown.get()

        # ex: 12L = 120, 36 = 360, 8 = 080 (padded zero not needed)
        runway_heading = int(runway[:2]) * 10

        # validate runway is in airport_info
        if runway in airport_info["Runways"].keys():
            surface = airport_info["Runways"][runway]["COMP_CODE"]
            surface = surface[:3]
        else:
            return self.open_errorwindow(message="Runway Error")
        
        if surface in "CONC" or surface in "ASPH":
            surface = "Paved"
        else:
            surface = "Grass"

        # get METAR XML file
        url = 'https://beta.aviationweather.gov/cgi-bin/data/dataserver.php?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=3&mostRecent=true&stationString='

        if len(airport) == 3:
            url += ('K' + airport)
        else:    
            url += airport
        
        try:
            response = urllib.request.urlopen(url)
        except BaseException:
            return self.open_errorwindow(message="Internet Error. Please restart application and use manual mode or try again.")
        data = response.read()

        # parse XML file
        root = et.fromstring(data)

        # find metar tag
        metar = root.find('.//METAR')
        
        data = {}
        elements = ['raw_text', 'temp_c', 'wind_dir_degrees', 'wind_speed_kt', 'altim_in_hg', 'wind_gust_kt', 'wx_string', 'precip_in']

        # get elements
        for element in elements:
            value = metar.findtext(element)
            data[element] = value

        # assign elements to variables
        elevation = int(round(float(airport_info["ELEVATION"])))
        temp_c, wind_dir, wind_speed, altimeter = int(round(float(data["temp_c"]))), int(data["wind_dir_degrees"]), int(data["wind_speed_kt"]), float(data["altim_in_hg"])
           
        try:
            gust_speed = int(data['wind_gust_kt'])
        # handle no wind gusts reported in METAR
        except TypeError:
            gust_speed = 0
        
        # alert user if wet runway is possible
        wt_rwy = False
        try:
            precip = data["wx_string"]
            if len(precip) > 2:
                precip = precip.split()[0]
                precip = precip[-2:]
            if precip in ['RA', 'SN', 'DZ', 'SH', 'GR', 'PY', 'PN', 'UP', 'BR']:
                wt_rwy = True
        # handle no precip info reported in METAR
        except TypeError:
            pass
        
        try:
            precip_amt = float(data["precip_in"])
            if precip_amt > 0:
                wt_rwy = True
        # handle no precip amount info reported in METAR
        except BaseException:
            pass

        # convert wind direction from true heading to magnetic heading
        lat1, lon1 = airport_info["Y"], airport_info["X"]

        # get magnetic declination data for airport coordinates
        url = f'https://www.ngdc.noaa.gov/geomag-web/calculators/calculateDeclination?lat1={lat1}&lon1={lon1}&key=zNEw7&resultFormat=xml'
        try:
            response = urllib.request.urlopen(url)
        except BaseException:
            return self.open_errorwindow(message="Internet Error. Please restart application and use manual mode or try again.")

        # parse xml
        root = et.fromstring(response.read())

        # find declination
        declination_element = root.find('.//declination')
        declination = int(round(float(declination_element.text.strip())))

        # convert wind direction from true heading to magnetic heading so both wind_dir and runway_heading are magnetic
        wind_dir += declination
        wind_dir = round(wind_dir, -1)

        # get TAF in raw_text
        local_taf = False
        if len(airport) == 4:
            url = 'https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&hoursBeforeNow=12&timeType=issue&mostRecent=true&stationString='
            url += airport
            local_taf = True
        else:
            # TAFs not available at all airports, find nearest TAF within 100 miles
            url = f'https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&radialDistance=100;{lon1},{lat1}&hoursBeforeNow=12&mostRecent=true'
        try:
            response = urllib.request.urlopen(url)
        except BaseException:
            return self.open_errorwindow(message="Internet Error. Please restart application and use manual mode or try again.")

        # parse xml
        root = et.fromstring(response.read())

        # find TAF raw_text
        taf = root.findtext('.//TAF/raw_text')

        # format TAF
        try:
            taf = taf.replace("FM", "\n          FM").replace("BECMG", "\n          BECMG").replace("TEMPO", "\n          TEMPO")
            if local_taf == False:
                taf = ("Local TAF not available. Nearest TAF:\n" + taf)
        # handle no TAF available
        except AttributeError:
            taf = "TAF not available"
    
    # calculate pressure altitude and ensure it is within chart bounds
    pa = int((29.92 - altimeter) * 1000 + elevation)
    if pa <= 0:
        pa = 0
    elif pa > 8000:
        return self.open_errorwindow(message="Pressure altitude above 8000ft. Takeoff distances undocumented.")
    
    # initialize weight and temp to be within POH table bounds
    # lower weight and lower temp only reduce takeoff distance
    if to_weight < 2200:
        to_weight = 2200
    if temp_c < 0:
        temp_c = 0
    elif temp_c > 40:
        return self.open_errorwindow(message="Temperature above 40°C. Takeoff distances undocumented.")

    # get initial distances
    distances = get_distances(to_weight, temp_c, pa)
    gnd_roll, obst, liftoff_speed, speed_at_fifty = distances[0], distances[1], distances[2], distances[3]
        
    # increase distances by 15% of ground roll if grass
    if surface == "Grass":
        a = gnd_roll
        gnd_roll *= 1.15
        gnd_roll_increase = gnd_roll - a
        obst += gnd_roll_increase

    # if wind calm no need to calculate wind effects
    if wind_speed > 1:
        # find headwind / tailwind component
        wind_angle = abs(wind_dir - runway_heading)
        if wind_angle > 180:
            wind_angle = abs(wind_angle - 360)
        component = abs(wind_speed * cos(wind_angle))
        gust_component = abs(gust_speed * cos(wind_angle))

        # decrease distances by 10% for every 9 knots of headwind component, no change if less than 9 knots of wind
        if wind_angle < 90:
            factor = 0.1 * (component // 9)
            gnd_roll -= ceil(factor * gnd_roll)
            obst -= ceil(factor * obst)
            
        # increase distances by 10% for every 2 knots of tailwind component (MAX 10kts)
        elif wind_angle > 90:
            if component > 10:
                return self.open_errorwindow(message="Tailwind component is greater than 10 knots. Different runway required.")
            else:
                factor = 0.1 * (component // 2)
                gnd_roll += ceil(factor * gnd_roll)
                obst += ceil(factor * obst)
    else:
        component, gust_component = 0, 0
    
    if mode == "MANUAL":
        # print takeoff distances and speeds
        self.result1.configure(text=f"{ceil(gnd_roll)} ft")
        self.result2.configure(text=f"{ceil(obst)} ft")
        self.liftoff_speed.configure(text=f"Liftoff Speed  –  {liftoff_speed} kts")
        self.speed_at_fifty.configure(text=f"Speed at 50ft  –  {speed_at_fifty} kts")
        
        # display leaning procedure note if pa > 3000ft
        if pa > 3000:
            self.note.grid(row=3, column=1, columnspan=2, pady=(12, 0), padx=20, sticky="nsew")
            self.lean.grid(row=4, column=1, columnspan=2, pady=(0, 12), padx=20, sticky="nsew")
        else:
            try:
                self.note.grid_forget()
                self.lean.grid_forget()
            except AttributeError:
                pass

    elif mode == "AUTO":
        # display weather, distances, speeds, and notes
        self.gndroll.configure(text=f"{ceil(gnd_roll)} ft")
        self.obst.configure(text=f"{ceil(obst)} ft")
        self.liftoff.configure(text=f"{liftoff_speed} kts")
        self.speed_at_fifty.configure(text=f"{speed_at_fifty} kts")
        self.metar.configure(text=data["raw_text"])
        self.taf.configure(text=taf)
        self.selected_runway_info.configure(text=f"RWY {runway}  |  Length: {airport_info['Runways'][runway]['LENGTH']}ft, Width: {airport_info['Runways'][runway]['WIDTH']}ft")

        if gnd_roll > int(airport_info['Runways'][runway]['LENGTH']):
            self.takeoff_distance_warning.grid(row=2, column=1, columnspan=2, padx=20, pady=10)
        else:
            try:
                self.takeoff_distance_warning.grid_forget()
            except AttributeError:
                pass
        if component < 10 and gust_component > 10:
            self.tailwind_note.grid(row=3, column=1, columnspan=2, padx=20, pady=10)
        else:
            try:
                self.tailwind_note.grid_forget()
            except AttributeError:
                pass
        if pa > 3000:
            self.pa_note.grid(row=4, column=1, columnspan=2, padx=20, pady=10)
        else:
            try:
                self.pa_note.grid_forget()
            except AttributeError:
                pass
        if wt_rwy:
            self.wt_rwy_note.grid(row=5, column=1, columnspan=2, padx=20, pady=10)
        else:
            try:
                self.wt_rwy_note.grid_forget()
            except AttributeError:
                pass
