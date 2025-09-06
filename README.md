# Takeoff Distance Calculator
Calculate takeoff distance for a Cessna 172S aircraft.

Airport and runway data retrieved from the FAA @ https://adds-faa.opendata.arcgis.com/  
Aviation weather data retrieved from the NWS @ https://beta.aviationweather.gov/data/example/  
Magnetic declination (variation) data from the NOAA @ https://www.ngdc.noaa.gov/geomag/CalcSurveyFin.shtml  
Video Demo: https://youtu.be/PS9F1ajYGcw

---
## Description
This program calculates the takeoff distances of a Cessna 172S aircraft, using Python and a Graphical User Interface (GUI) created with CustomTkinter, a modification of Tkinter. There are two modes available: Auto Mode and Manual Mode. 

## Auto Mode
Auto Mode is a Python program that uses several packages to access 3 internet sources, 2 local files, and 1 SQL database. When the user selects "Auto Mode" on the GUI's initial screen, the program calls 'open_automode' to reformat the GUI and display the relevant information. The program then prompts the user to enter 3 parameters and, upon clicking the "Calculate" button, presents a variety of information. This includes current and forecasted weather, takeoff distances and speeds, runway details, and notes on takeoff conditions.

On the left sidebar of the GUI, the user enters the Airport ID in ICAO format. This is a code used by pilots to identify airports worldwide, with most US airports beginning with 'K', followed by a code related to the airport name. Smaller airports may have a one-letter code followed by two numbers, sometimes related to the state name. For instance, 'KPHX' is the ICAO code for Phoenix Sky Harbor International Airport, while 'P08' is the code for Coolidge Municipal Airport in Coolidge, AZ.

After the user changes their focus from the airport entry, 'get_runways_info' is called from 'utilites.py' and the program searches the Comma Separated Values (CSV) files for the airport and runways, retrieving relevant information. The two local CSV files are extensive, containing tens of thousands of lines of data on every airport and runway in the US. The sidebar is then updated to display the airport's name, location, and elevation, which allows the user to verify the accuracy of their input. The 'Runway' dropdown selection is updated with the runways available at the selected airport. The files from the Federal Aviation Administration (FAA) sometimes are not formatted correctly for this program’s use, so some extra calculation is needed to ensure the user can select any of the runways at the airport.

Next, the user enters their aircraft's takeoff weight, which the program validates to ensure it's less than the maximum takeoff weight for the Cessna 172S (C172) and more than the typical minimum weight for a C172. The user then selects the intended runway from the 'Runway' dropdown box. Unknown to the user, the selection was updated after the focus was changed from the airport entry.

Lastly, the user clicks "Calculate" to call 'calculate' from 'calculate.py' and start the calculation process.
  
## Manual Mode
Manual Mode requires the user to enter 8 parameters, including takeoff weight, temperature, wind direction, wind speed, airport elevation, runway heading, altimeter, and runway type (paved or grass). All parameters are easily accessible outside of the program, except for runway heading, which must be in true heading format. In aviation, any time wind direction is "read" rather than "heard" the format is in true heading. To calculate the component of the wind that affects takeoff distance, both the wind direction and runway heading must be in the same format. In this mode, no additional code is executed until the user selects the "Calculate" button.

## Calculation
'calculate' is called from 'main.py' with an argument of either "MANUAL" or "AUTO". In the case of "MANUAL" mode, the program validates user entries by calling the 'validate' function to ensure proper ranges and values. If an invalid entry is detected, the calculation is stopped, and an error message is displayed by calling 'open_errorwindow'.

In "AUTO" mode the 'calculate' function gathers all information that the user would have provided in manual mode. First, takeoff weight is validated, and runway heading is calculated. Runways are named based on their magnetic heading, and sometimes have a letter suffix that is based on their relation to other runways of the same magnetic heading. To get runway heading, the program takes the numbers times 10 to get the magnetic heading in degrees. The runway's information is then referenced to find the runway type (paved or grass). An Application Programming Interface (API) from the National Weather Service (NWS) is then used to get the airport's current weather, referred to in aviation as the METeorological Aerodrome Report (METAR). The API returns the information in Extensible Markup Language (XML). The program parses the XML document and assigns variables based on the information gathered. If the temperature is higher than 40°C, the highest temperature recorded on the takeoff distance chart, the user is notified. Since takeoff distances are only valid if the runway is dry, the program checks for precipitation and precipitation amounts for the last 6 hours. If a wet runway is possible, a note will be displayed. Next, the airports coordinates are plugged into an API from the National Oceanic and Atmospheric Association (NOAA). This returns information regarding the magnetic declination, referred to in aviation as magnetic variation. The program uses that data to convert wind direction from true heading to magnetic heading. Lastly, the API from the NWS is used to get the Terminal Area Forecast (TAF). Since TAFs aren't available at every airport, the program also finds the nearest TAF if one isn't available. The TAF isn't used in any part of the calculation, however it is displayed to the user as a convenience.

Manual mode and auto mode follow the same path for the remainder of the calculation. The program calculates pressure altitude using atmospheric pressure in inches of mercury, referred to as the altimeter in aviation. Next, takeoff weight and temperature are verified to be within the correct bounds of the takeoff distance chart. Since takeoff distance is reduced by a lower takeoff weight or a lower temperature, to keep the values within bounds of the chart, the program assigns weight and temperature to the lowest bound of the chart if necessary. From here, the program calls 'get_distances' from 'utilites.py' to get the initial distances from the SQL database. If the surface is grass, the distances are increase by 15% of the ground roll. Next, the wind effects are calculated if the wind speed is not calm. Takeoff distance is reduced by 10% for every 9 knots of headwind component and decreased by 10% for every 2 knots of tailwind component, with a maximum of 10 knots. The program uses trigonometry to calculate the speed of component of the wind that is a headwind or tailwind. 

Finally, the program displays the takeoff distances and appropriate speeds, along with any relevant notes depending on the mode. If pressure altitude is greater than 3000ft, the user is reminded to appropriately configure the engine for high altitude performance before takeoff. In the special case of a sustained tailwind component that is less than 10 knots but a tailwind gust component that is greater than 10 knots, the user is notified to monitor the winds and use extreme caution. Lastly, if the ground roll is greater than the runway distance, the user is advised not to takeoff using the selected runway.

## SQL Database & Interpolation
This program references takeoff performance data from the aircraft's manufacturer, Cessna in this case. This data is located in the aircraft's Pilot's Operating Handbook (POH). The performance information is stored in a local SQL database called 'data'. View 'SQL.txt' for the schema and tables. The 'get_distances' function in 'utilities.py' initializes the SQL query elements based on the values of weight, temperature, and pressure altitude, and determines if interpolation is required for any of these variables. Interpolation is necessary when a variable does not exactly align with a column or row on the POH's takeoff distance chart. The interpolation process uses a simple algorithm that queries the nearest lower and higher rows or columns as needed. For example, when 'interpolate_temp' is called, it initially queries the lower pressure altitude row. Next, when 'interpolate_pa' is called, that function calls 'interpolate_temp' but this time querying the higher pressure altitude row. The same is true if weight interpolation is required. The same process happens again, this time for the higher weight table.

Although SQL would not typically be appropriate for this application, I decided to use it in this context to demonstrate SQL proficiency. The performance data would have been more appropriately stored in a CSV file.

---
### Auto Mode

![Screenshot 2023-03-01 152316](https://user-images.githubusercontent.com/122923063/222279343-37b78d68-8da6-4a04-840e-a42920b8cb9c.png)

#

### Manual Mode

![Screenshot 2023-02-26 154940](https://user-images.githubusercontent.com/122923063/221442286-a4803f62-ecda-4b2b-821e-338bad4aff62.png)
