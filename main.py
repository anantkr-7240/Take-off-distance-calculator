from calculate import calculate
import customtkinter
from utilites import get_runways_info


# airport and runway data retrieved from the FAA @ https://adds-faa.opendata.arcgis.com/
# aviation weather data retrieved from the NWS @ https://beta.aviationweather.gov/data/example/
# magnetic declination (magnetic variation) data from the NOAA @ https://www.ngdc.noaa.gov/geomag/CalcSurveyFin.shtml


class ErrorWindow(customtkinter.CTkToplevel):
    def __init__(self, message):
        super().__init__()
        self.minsize(400, 150)
        self.title("Error")

        self.label = customtkinter.CTkLabel(self, text="Error", font=customtkinter.CTkFont(size=26, weight="bold"))
        self.label.pack(padx=30, pady=(20, 0))

        self.error_msg = customtkinter.CTkLabel(self, text=message, font=customtkinter.CTkFont(size=16))
        self.error_msg.pack(padx=30, pady=20)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("dark-blue")

        self.error_window = None
        self.title("C172S Takeoff Distance")
        self.minsize(400, 300)

        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.grid_rowconfigure((1, 2), weight=1)
        self.grid_rowconfigure((0, 3), weight=50)

        self.autobutton = customtkinter.CTkButton(master=self, command=self.open_automode, text="Auto Mode")
        self.autobutton.grid(row=1, column=1, columnspan=2, padx=12, pady=12)
        self.manualbutton = customtkinter.CTkButton(master=self, command=self.open_manualmode, text="Manual Mode")
        self.manualbutton.grid(row=2, column=1, columnspan=2, padx=12, pady=12)


    def open_automode(self):
        #region Configure
        self.autobutton.destroy()
        self.manualbutton.destroy()
        self.minsize(1600, 800)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure((1, 2, 3, 4), weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        #endregion

        #region Sidebar Frame
        self.sidebar_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(8, weight=20)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="C172S Takeoff Distance", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.airport_label = customtkinter.CTkLabel(master=self.sidebar_frame, text="Airport (ICAO)", font=customtkinter.CTkFont(size=14))
        self.airport_label.grid(row=1, column=0, padx=20, pady=(20, 2))
        self.airport_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Airport (ICAO)", font=customtkinter.CTkFont(size=12))
        self.airport_entry.grid(row=2, column=0, padx=20, pady=(2, 12))
        self.airport_entry.bind(sequence='<FocusOut>', command=self.get_runways_info_callback)

        self.airport_label = customtkinter.CTkLabel(master=self.sidebar_frame, text="Takeoff Weight (lbs)", font=customtkinter.CTkFont(size=14))
        self.airport_label.grid(row=3, column=0, padx=20, pady=(8, 2))
        self.weight_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Takeoff Weight (lbs)", font=customtkinter.CTkFont(size=12))
        self.weight_entry.grid(row=4, column=0, padx=20, pady=(2, 12))

        # airport entry defines values for runway_dropdown, get_runways_info is called on airport entry focus out to update values of combox box
        self.runway_dropdown = customtkinter.CTkOptionMenu(master=self.sidebar_frame, values=[], fg_color="#545454", button_color="#545454", 
                                                           button_hover_color="#424242", width=50)
        self.runway_dropdown.grid(row=5, column=0, padx=20, pady=12)
        self.runway_dropdown.set("Runway")

        self.airportinfo_label = customtkinter.CTkLabel(master=self.sidebar_frame, text="Airport Information", font=customtkinter.CTkFont(size=16))
        self.airportinfo_label.grid(row=6, column=0, padx=20, pady=(12, 4))
        self.airportinfo = customtkinter.CTkLabel(master=self.sidebar_frame, text="", font=customtkinter.CTkFont(size=14), justify="left")
        self.airportinfo.grid(row=7, column=0, padx=20, pady=4)

        # row 8 weight 20 to push calc button to the bottom 

        self.calc_button = customtkinter.CTkButton(master=self.sidebar_frame, command=self.calc_auto, text="Calculate")
        self.calc_button.grid(row=9, column=0, pady=20, padx=20)
        #endregion

        #region Weather Tab
        self.weather = customtkinter.CTkTabview(self, segmented_button_selected_color="#545454", segmented_button_selected_hover_color="#545454")
        self.weather.grid(row=0, column=1, columnspan=4, padx=20, pady=20, sticky="nsew")
        self.weather.add("Weather")
        self.weather.tab("Weather").grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.weather.tab("Weather").grid_columnconfigure((1, 2), weight=1)
        self.weather.tab("Weather").grid_columnconfigure((0, 3), weight=10)

        self.metar_label = customtkinter.CTkLabel(master=self.weather.tab("Weather"), text="METAR", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.metar_label.grid(row=0, column=1, columnspan=2, padx=20, pady=(20, 4))
        self.metar = customtkinter.CTkLabel(master=self.weather.tab("Weather"), text="", font=customtkinter.CTkFont(size=14))
        self.metar.grid(row=1, column=1, columnspan=2, padx=20, pady=(4, 10))

        self.taf_label = customtkinter.CTkLabel(master=self.weather.tab("Weather"), text="TAF", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.taf_label.grid(row=2, column=1, columnspan=2, padx=20, pady=(10, 4))
        self.taf = customtkinter.CTkLabel(master=self.weather.tab("Weather"), text="", font=customtkinter.CTkFont(size=14), justify="left")
        self.taf.grid(row=3, column=1, columnspan=2, padx=20, pady=(4, 20))
        #endregion

        #region Distances Frame
        self.distances_frame = customtkinter.CTkFrame(self, width=200)
        self.distances_frame.grid(row=1, column=1, columnspan=2, padx=20, pady=20, sticky="nsew")
        self.distances_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.distances_frame.grid_columnconfigure((1, 2), weight=1)
        self.distances_frame.grid_columnconfigure((0, 3), weight=20)

        self.gndroll_label = customtkinter.CTkLabel(self.distances_frame, text="Ground Roll", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.gndroll_label.grid(row=0, column=1, columnspan=2, padx=20, pady=20)
        self.gndroll = customtkinter.CTkLabel(self.distances_frame, text="", font=customtkinter.CTkFont(size=16)) # configure gndroll in calculate function
        self.gndroll.grid(row=1, column=1, columnspan=2, padx=20, pady=20)

        self.obst_label = customtkinter.CTkLabel(self.distances_frame, text="Clear 50ft Obstacle", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.obst_label.grid(row=3, column=1, columnspan=2, padx=0, pady=20)
        self.obst = customtkinter.CTkLabel(self.distances_frame, text="", font=customtkinter.CTkFont(size=16)) # configure obst in calculate function
        self.obst.grid(row=4, column=1, columnspan=2, padx=20, pady=20)
        #endregion

        #region Speeds Frame
        self.speeds_frame = customtkinter.CTkFrame(self, width=800)
        self.speeds_frame.grid(row=1, column=3, columnspan=2, padx=20, pady=20, sticky="nsew")
        self.speeds_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.speeds_frame.grid_columnconfigure((1, 2), weight=1)
        self.speeds_frame.grid_columnconfigure((0, 3), weight=20)

        self.liftoff_label = customtkinter.CTkLabel(self.speeds_frame, text="Liftoff Speed", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.liftoff_label.grid(row=0, column=1, columnspan=2, padx=20, pady=20)
        self.liftoff = customtkinter.CTkLabel(self.speeds_frame, text="", font=customtkinter.CTkFont(size=16)) # configure liftoff in calculate function
        self.liftoff.grid(row=1, column=1, columnspan=2, padx=20, pady=20)

        self.speed_at_fifty_label = customtkinter.CTkLabel(self.speeds_frame, text="Speed at 50ft", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.speed_at_fifty_label.grid(row=3, column=1, columnspan=2, padx=30, pady=20)
        self.speed_at_fifty = customtkinter.CTkLabel(self.speeds_frame, text="", font=customtkinter.CTkFont(size=16)) # configure speed_at_fifty in calculate function
        self.speed_at_fifty.grid(row=4, column=1, columnspan=2, padx=20, pady=20)
        #endregion

        #region Notes Tab
        self.notes = customtkinter.CTkTabview(self, segmented_button_selected_color="#545454", segmented_button_selected_hover_color="#545454")
        self.notes.grid(row=2, rowspan=2, column=1, columnspan=4, padx=20, pady=20, sticky="nsew")
        self.notes.add("Notes")
        self.notes.tab("Notes").grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.notes.tab("Notes").grid_columnconfigure((1, 2), weight=1)
        self.notes.tab("Notes").grid_columnconfigure((0, 3), weight=10)

        self.selected_runway_info = customtkinter.CTkLabel(master=self.notes.tab("Notes"), text="", font=customtkinter.CTkFont(size=14))
        self.selected_runway_info.grid(row=0, column=1, columnspan=2, padx=20, pady=10)

        self.to_distance_warning = customtkinter.CTkLabel(master=self.notes.tab("Notes"), text="", font=customtkinter.CTkFont(size=14))
        self.to_distance_warning.configure(text="WARNING: Takeoff distance shorter than runway length. TAKEOFF NOT ADVISED.")

        self.conditions = customtkinter.CTkLabel(master=self.notes.tab("Notes"), 
                                                 text="Conditions: Flaps 10° | Full throttle prior to brake release | Level, Dry Runway", 
                                                 font=customtkinter.CTkFont(size=14))
        self.conditions.grid(row=2, column=1, columnspan=2, padx=20, pady=10)

        self.tailwind_note = customtkinter.CTkLabel(master=self.notes.tab("Notes"), text="", font=customtkinter.CTkFont(size=14))
        self.tailwind_note.configure(
            text="Sustained tailwind component is less than 10kts but tailwind gust component is greater than 10kts. Monitor winds and use extreme caution.")

        self.pa_note = customtkinter.CTkLabel(master=self.notes.tab("Notes"), font=customtkinter.CTkFont(size=14))
        self.pa_note.configure(text="Pressure altitude above 3000ft -- the mixture should be\nleaned to give maximum RPM in a full throttle, static run-up.")

        self.wt_rwy_note = customtkinter.CTkLabel(master=self.notes.tab("Notes"), text="", font=customtkinter.CTkFont(size=14))
        self.wt_rwy_note.configure(text="Possible wet runway -- takeoff distances are invalid if runway is wet.")
        #endregion


    def open_manualmode(self):
        self.autobutton.destroy()
        self.manualbutton.destroy()

        # configure grid layout (2x2)
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        #region Entries Frame
        self.frame = customtkinter.CTkFrame(master=self)
        self.frame.grid(row=0, column=0, rowspan=2, pady=20, padx=20, sticky="nsew")
        self.frame.grid_columnconfigure((1, 2), weight=1)
        self.frame.grid_columnconfigure((0, 4), weight=50)
        self.frame.grid_rowconfigure((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 ,14, 15, 16, 17), weight=1)
        self.frame.grid_rowconfigure((0, 18), weight=200)

        self.label = customtkinter.CTkLabel(master=self.frame, text="Takeoff Distance Calculator", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.label.grid(row=1, column=1, columnspan=2, pady=24, padx=20, sticky="nsew")

        text = ["Takeoff Weight (lbs)", "Temperature (°C)", "Wind Direction (True Heading)", "Wind Speed (knots)",
        "Airport Elevation (ft)", "Runway Heading (True Heading)", "Altimiter (in/hg)"]

        # make labels and entries from the list of text, assign to a row from 2-15
        for i, t in enumerate(text, start=1):
            label_row = ((i - 1) * 2) % 15 + 2
            entry_row = ((i - 1) * 2 + 1) % 15 + 2

            label = customtkinter.CTkLabel(master=self.frame, text=t, height=10, width=100, font=customtkinter.CTkFont(size=12))
            label.grid(row=label_row, column=1, columnspan=2, pady=2, padx=20, sticky="nsew")
            setattr(self, f"label{i}", label)

            entry = customtkinter.CTkEntry(master=self.frame, placeholder_text=t, width=225, font=customtkinter.CTkFont(size=12))
            entry.grid(row=entry_row, column=1, columnspan=2, pady=12, padx=20, sticky="nsew")
            setattr(self, f"entry{i}", entry)

        self.combobox = customtkinter.CTkOptionMenu(master=self.frame, values=["Paved", "Grass"], fg_color="#545454", button_color="#545454", 
                                                    button_hover_color="#424242" , width=50)
        self.combobox.grid(row=16, column=1, columnspan=2, padx=20, pady=(10, 20), sticky="nsew")
        self.combobox.set("Runway Surface")

        self.button = customtkinter.CTkButton(master=self.frame, command=self.calc_manual, text="Calculate")
        self.button.grid(row=17, column=1, columnspan=2, padx=20, pady=(10, 20), sticky="nsew")
        #endregion

        #region Distances Frame
        self.frameright = customtkinter.CTkFrame(master=self)
        self.frameright.grid(row=0, column=1, rowspan=1, pady=20, padx=20, sticky="nsew")
        self.frameright.grid_columnconfigure((1, 2), weight=1)
        self.frameright.grid_columnconfigure((0, 4), weight=50)
        self.frameright.grid_rowconfigure((1, 2, 3, 4), weight=1)
        self.frameright.grid_rowconfigure((0, 5), weight=200)

        self.result_title1 = customtkinter.CTkLabel(master=self.frameright, text="Ground Roll", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.result_title1.grid(row=1, column=1, columnspan=2, pady=12, padx=20, sticky="nsew")

        self.result1 = customtkinter.CTkLabel(master=self.frameright, text="", font=customtkinter.CTkFont(size=16))
        self.result1.grid(row=2, column=1, columnspan=2, pady=12, padx=10, sticky="nsew")

        self.result_title2 = customtkinter.CTkLabel(master=self.frameright, text="Clear 50ft Obstacle", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.result_title2.grid(row=3, column=1, columnspan=2, pady=12, padx=20, sticky="nsew")

        self.result2 = customtkinter.CTkLabel(master=self.frameright, text="", font=customtkinter.CTkFont(size=16))
        self.result2.grid(row=4, column=1, columnspan=2, pady=12, padx=10, sticky="nsew")
        #endregion

        #region Speeds & Notes Frame
        self.frame_bottom_right = customtkinter.CTkFrame(master=self)
        self.frame_bottom_right.grid(row=1, column=1, rowspan=1, pady=20, padx=20, sticky="nsew")
        self.frame_bottom_right.grid_columnconfigure((1, 2), weight=1)
        self.frame_bottom_right.grid_columnconfigure((0, 4), weight=50)
        self.frame_bottom_right.grid_rowconfigure((1, 2, 3, 4, 5), weight=1)
        self.frame_bottom_right.grid_rowconfigure((0, 6), weight=200)

        self.liftoff_speed = customtkinter.CTkLabel(master=self.frame_bottom_right, text="Liftoff Speed", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.liftoff_speed.grid(row=0, column=1, columnspan=2, pady=20, padx=20, sticky="nsew")
        
        self.speed_at_fifty = customtkinter.CTkLabel(master=self.frame_bottom_right, text="Speed at 50ft", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.speed_at_fifty.grid(row=1, column=1, columnspan=2, pady=20, padx=20, sticky="nsew")

        self.conditions = customtkinter.CTkLabel(master=self.frame_bottom_right, 
                                                 text="Conditions: Flaps 10° | Full throttle prior to brake release | Level, Dry Runway", 
                                                 font=customtkinter.CTkFont(size=16))
        self.conditions.grid(row=2, column=1, columnspan=2, pady=(30, 0), padx=40, sticky="nsew")

        self.note = customtkinter.CTkLabel(master=self.frame_bottom_right, text="Note: Pressure altitude above 3000ft -- the mixture should be", 
                                           font=customtkinter.CTkFont(size=16))
        self.lean = customtkinter.CTkLabel(master=self.frame_bottom_right, text="leaned to give maximum RPM in a full throttle, static run-up.", 
                                           font=customtkinter.CTkFont(size=16))
        #endregion


    # customtkinter command requirement
    def calc_manual(self):
        calculate(self, mode="MANUAL")
    
    # customtkinter command requirement
    def calc_auto(self):
        calculate(self, airport_info, mode="AUTO")

    
    # currentvalue is unused due to customtkinter requirements, currentvalue = <FocusOut> Event
    def get_runways_info_callback(self, currentvalue):
        global airport_info 
        airport_info = get_runways_info(self)

    
    def open_errorwindow(self, message):
        if self.error_window is None or not self.error_window.winfo_exists():
            self.error_window = ErrorWindow(message) # create window if its None or destroyed
            self.error_window.grab_set()
        else:
            # if window exists focus it
            self.error_window.grab_set()


if __name__ == "__main__":
    app = App()
    app.mainloop()
