import random
import tkinter
from tkinter import *
from tkinter import ttk
import time
import re
import datetime
import string

# Import main tk window object to Instantiate root window
from parent import root as par

import sqlite3


# Global root window variable (later assigned in "run" func)
root = None

# Custom main dataset (flight records list)
flight_records = []

filtered_dataset = flight_records
# Filtering parameters
filter_pars = dict()
# In case of successful ticket reservation, this object holds data to be committed (stored) to database
# (This is actually a dictionary of dictionaries, each internal dictionary corresponds to a table which holds
# its records)
to_be_committed = dict()

# tkinter boolVar to switch tour/passenger panel (launch corresponding handlers)
tour = BooleanVar(value=False)
# tkinter boolVar to launch reservation handlers
reserve_var = BooleanVar(value=False)
# tkinter boolVar to track tour mode reserve (since reserve func
# need to be executed twice, each time with different procedure.)
round_tour = False
# Variable to track existence of any error, and the type of it based on custom defined error codes
error_type = 0
# Trigger function to display error type (always of first found error), and remove it
error_flag = tkinter.BooleanVar(value=False)
# Tkinter BoolVar to setup mechanism to enable a global cleaning system
global_cleaner = BooleanVar(value=False)



class AutocompleteEntry(Entry):

    def __init__(self, root, autocompleteList, *args, entry_for=None, set_focus=False, **kwargs):
        # Static func to map to <FocusOut> event within init
        # (to destroy listbox when clicking elsewhere or switching between entries)
        def remove_listbox(even_type):
            if self.listboxUp:
                self.listbox.destroy()
                self.listboxUp = False

        # Holds value for root window (in fact topnotch type)
        self.root = root
        # Holds address to external method to set ticket cost.
        self.priceTag_set = None
        # Variables to use for connection with table
        # (holding list index of each parameter in flight_records dataset)
        self.entry_for = entry_for
        self.table_func = None
        # Flag to control listbox
        # (Set to prevent listbox to open up, and is disabled to let it open up.
        # It is useful when setting filled values automatically, eg, smart table.)
        self.flag_value_control = False

        # Set Listbox length
        if 'listboxLength' in kwargs:
            self.listboxLength = kwargs['listboxLength']
            del kwargs['listboxLength']
        else:
            self.listboxLength = 8

        # Custom matches function (if passed withing args)
        if 'matchesFunction' in kwargs:
            self.matchesFunction = kwargs['matchesFunction']
            del kwargs['matchesFunction']
        else:
            # Default matching func using regex
            def matches(fieldValue, acListEntry):
                pattern = re.compile('.*' + re.escape(fieldValue) + '.*', re.IGNORECASE)
                return re.match(pattern, acListEntry)

            self.matchesFunction = matches
        # Instantiate/initialize "entry" obj
        Entry.__init__(self, *args, **kwargs)
        # self.config(highlightbackground="red")
        if set_focus:
            self.focus()

        # a column/Subset global dataset based of entry type passed as arg. (eg, id, origin, destination, airplane ..)
        self.autocompleteList = autocompleteList

        self.var = self["textvariable"]
        if self.var == '':
            self.var = self["textvariable"] = StringVar()

        self.var.trace('w', self.changed)
        self.bind("<Right>", self.selection)
        self.bind("<Up>", self.moveUp)
        self.bind("<Down>", self.moveDown)
        self.bind("<FocusOut>", remove_listbox)

        self.listboxUp = False

    # This method is called whenever a character is entered.
    # (This function is mapped to entry in init, using a tkinter varString trace method.)
    def changed(self, name, index, mode):
        # Variable to track autocompleted entries
        global filter_pars
        # Override border color to normal (in case of an error it turns to red)
        self.config(highlightbackground='lightgrey')
        # Delete Error box in case of any change
        error_flag.set(False)
        # Control autocomplete functionality (this prevents listbox from executing if the completed values
        # are being inserted directly from table rows being clicked or a zero length string is being inserted.)
        if self.var.get() == '':
            # if self.var.get() == '' and self.flag_value_control == False:
            # Updated filtered dataset list and call corresponding method to update the actual dataset
            if self.entry_for in filter_pars.keys():
                filter_pars.pop(self.entry_for)

            self.dataset_filter()
            # Check if listbox is already up (not the first char entered), kill it
            if self.listboxUp:
                self.listbox.destroy()
                self.listboxUp = False
        # Control autocomplete functionality (this prevents listbox from executing if the completed values
        # are being inserted directly from table rows being clicked.)
        elif self.flag_value_control == False:
            words = self.comparison()
            # Updated filtered dataset list and call corresponding method to update the actual dataset
            filter_pars[self.entry_for] = set(words)
            # Run filtering method
            self.dataset_filter()
            # Check if any word is matched in regex process
            if words:
                # Check if listbox obj is already launched then run it
                if not self.listboxUp:
                    self.listbox = Listbox(self.root, width=self["width"], height=self.listboxLength)
                    # Map handling funcs to events. (eg, when a row/item is click from the listbox..)
                    self.listbox.bind("<Button-1>", self.selection)
                    self.listbox.bind("<Right>", self.selection)
                    # self.listbox.place(x=self.winfo_x(), y=self.winfo_y() + self.winfo_height())
                    self.listbox.place(x=(2 * self.winfo_x())+35, y=self.winfo_y() + (14 * self.winfo_height())-3)
                    self.listboxUp = True
                # After Making listbox object, remove all previous row, and print all new ones
                self.listbox.delete(0, END)
                for w in words:
                    self.listbox.insert(END, w)
                # In case of a completed id, we want to populate all entries with values instantly
                if self.entry_for == 6:
                    self.priceTag_set(listbox=self.listboxUp)
            # If listbox obj already exist, destroy it
            else:
                if self.listboxUp:
                    self.listbox.destroy()
                    self.listboxUp = False

    # Method to kill the listbox. (when one item/row in listbox is being clicked)
    def selection(self, event):
        # Check if listbox is up, then kill it.
        if self.listboxUp:
            self.var.set(self.listbox.get(ACTIVE))
            self.listbox.destroy()
            self.listboxUp = False
            self.icursor(END)
        # In case of an "id" entry run price tag.
        if self.entry_for == 6:
            self.priceTag_set()

    def moveUp(self, event):
        if self.listboxUp:
            if self.listbox.curselection() == ():
                index = '0'
            else:
                index = self.listbox.curselection()[0]

            if index != '0':
                self.listbox.selection_clear(first=index)
                index = str(int(index) - 1)

                self.listbox.see(index)  # Scroll!
                self.listbox.selection_set(first=index)
                self.listbox.activate(index)

    def moveDown(self, event):
        if self.listboxUp:
            if self.listbox.curselection() == ():
                index = '0'
            else:
                index = self.listbox.curselection()[0]

            if index != END:
                self.listbox.selection_clear(first=index)
                index = str(int(index) + 1)

                self.listbox.see(index)  # Scroll!
                self.listbox.selection_set(first=index)
                self.listbox.activate(index)

    # It returns a list of matched words.
    # (Basically it iterates through passed autocomplete list, and checks if they matched with
    # entered characters/entry.get , the actual regex matching function is implemented inside
    # init, and stored in self.matchesFunction.)
    def comparison(self):
        return [w for w in self.autocompleteList if self.matchesFunction(self.var.get(), w)]

    # For integration with smart_table.
    # (All it does is storing, smart_table's draw methods address)
    def set_table_func_addr(self, addr):
        self.table_func = addr

    # For integration with parent function
    # (Basically tracking method which sets label text=cost of flight id.)
    def set_priceTag_method_addr(self, addr):
        self.priceTag_set = addr

    # For integration with smart_table, so when each character entered it updates dataset,
    # based on filtered info and calls smart_table to update printing items.
    def dataset_filter(self):
        global filtered_dataset
        filtered_dataset = flight_records
        for key, values in filter_pars.items():
            temp_dataset = []
            for word in values:

                for item in [attr_row for attr_row in filtered_dataset if attr_row[key] == word]:
                    temp_dataset.append(item)
            filtered_dataset = temp_dataset

        self.table_func.draw()

    # For integration with smart_table, so when a row (flight record) is selected,
    # this method is externally called and fills up entries, with flight details.
    def set_value(self, value):
        self.flag_value_control = True
        self.var.set(value)
        self.flag_value_control = False
        # In case of an "id" entry run price tag.
        if self.entry_for == 6:
            self.priceTag_set(value)

    # This function clears out flight options.
    # (in manually filled, entries autocomplete, or tables auto select fields)
    def cleaner(self):
        self.flag_value_control = True
        self.var.set('')
        self.flag_value_control = False


class SmartTable(ttk.Treeview):
    def __init__(self, *args, **kwargs):
        self.selected_item = None
        self.id_option = None
        self.src_option = None
        self.dst_option = None
        self.airline_option = None
        self.plane_option = None
        self.price_option = None
        self.date_option = None
        ttk.Treeview.__init__(self, *args, **kwargs)

        self.columns_config()
        self.style_config()
        self.draw()
        self.bind('<ButtonRelease-1>', self.select_filter)

    def select_filter(self, event_descriptor):
        new_selected_item = self.focus()
        if new_selected_item and (new_selected_item != self.selected_item):
            self.selected_item = new_selected_item
        if self.item(new_selected_item)["values"]:
            date, src, dst, airline, plane, price, id = self.item(new_selected_item)["values"]
            self.src_option.set_value(src)
            self.dst_option.set_value(dst)
            self.airline_option.set_value(airline)
            self.plane_option.set_value(plane)
            self.id_option.set_value(id)

    def set_options_func_addr(self, id=None, src=None, dst=None, airline=None, plane=None, date=None, price=None):
        self.id_option = id
        self.src_option = src
        self.dst_option = dst
        self.airline_option = airline
        self.plane_option = plane

    def columns_config(self):
        # Remove First empty column header
        self['show'] = 'headings'
        # Set columns
        self["columns"] = "date", "src", "dst", "airline", "plane", "price", "id"
        # Set Columns attrs, eg. positioning(anchor)
        self.column("dst", anchor=CENTER, width=80)
        self.column("src", anchor=CENTER, width=80)
        self.column("airline", anchor=CENTER, width=90)
        self.column("plane", anchor=CENTER, width=90)
        self.column("date", anchor=CENTER, width=110)
        self.column("price", anchor=CENTER, width=80)
        self.column("id", anchor=CENTER, width=100)
        # Set column headings attr, eg. text
        self.heading("date", text="Date", anchor=CENTER)
        self.heading("src", text="Origin", anchor=CENTER)
        self.heading("dst", text="Destination", anchor=CENTER)
        self.heading("airline", text="Airline", anchor=CENTER)
        self.heading("plane", text="Airplane", anchor=CENTER)
        self.heading("price", text="Price", anchor=CENTER)
        self.heading("id", text="ID", anchor=CENTER)

    def style_config(self):
        # Create an instance of Style widget
        style = ttk.Style()
        # Pick a theme
        style.theme_use("default")
        # Configure Treeview colors
        # style.configure("Treeview", backgroud="silver", foreground="black", rowheight=25, fieldbackgrund="silver")
        # style.map("Treeview", background=[("selected", "green")])
        style.map("Treeview")

    def draw(self):
        # Clear table
        for item in self.get_children():
            self.delete(item)
        # Feeling up the table using database values
        for index, flight_record in enumerate(filtered_dataset):
            if index % 2 == 0:
                self.insert(parent='', index=END, values=flight_record, tags="odd_row")
            else:
                self.insert(parent='', index=END, values=flight_record, tags="even_row")
        # Make rows "striped(two consecutive rows with different colors)"
        self.tag_configure("even_row", background="lightblue")


def load_db():
    global flight_records
    try:
        connection = sqlite3.connect("Airport.db")
        cursor = connection.cursor()

        # Query plane list from database
        sql_query = """SELECT * FROM airplane"""
        cursor.execute(sql_query)
        # Construct plane list
        plane_dict = {}
        fetched_record = cursor.fetchone()
        while fetched_record:
            plane_dict.update({fetched_record[0]: fetched_record[1:]})
            fetched_record = cursor.fetchone()

        # Query airline list from database
        sql_query = """SELECT * FROM airline"""
        cursor.execute(sql_query)
        # Construct airline list
        airline_dict = {}
        fetched_record = cursor.fetchone()
        while fetched_record:
            airline_dict.update({fetched_record[0]: fetched_record[1:]})
            fetched_record = cursor.fetchone()

        # Query flight list from database
        sql_query = """SELECT * FROM flight"""
        cursor.execute(sql_query)
        # flight_records_dict = cursor.fetchall()
        flight_records_dict = {}
        # Construct flight list in required order
        order_list = [3, 1, 2, 5, 4, 8, 0]  # order: id, origin, dest, plane, airline, price, id
        fetched_record = cursor.fetchone()
        while fetched_record:
            flight_records_dict.update({fetched_record[0]: [fetched_record[order] for order in order_list]})

            flight_records_dict[fetched_record[0]][3] = airline_dict[fetched_record[6]][0]
            flight_records_dict[fetched_record[0]][4] = plane_dict[fetched_record[5]][0]
            # flight_records_dict.update({fetched_record[0]: fetched_record[1:]})
            fetched_record = cursor.fetchone()

        cursor.close()

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)

        # Invoke error handling procedure
        global error_type
        error_type = 4
        error_flag.set(True)

    finally:
        if connection:
            print("Total Rows affected since the database connection was opened: ", connection.total_changes)
            connection.close()
            print("sqlite connection is closed")

    # Print only useful records
    thisMonth = datetime.date.today().strftime('%b').lower()
    thisDay = int(datetime.date.today().strftime('%d'))

    for record_key in flight_records_dict:
        month = flight_records_dict[record_key][0].split()[1].lower()
        day = int(flight_records_dict[record_key][0].split()[2])
        if thisMonth != month:
            pass
        elif day < thisDay:
            pass
        else:
            flight_records.append(flight_records_dict.get(record_key))


def render_root(root):
    # Set window size
    root.geometry("1000x700")
    # root.geometry("530x600")
    # Set title
    root.title("Reserve Flight")
    # Make window size fixed
    root.resizable(False, False)
    # Set root window color
    root.config(background="#c4d1de")
    # root.config(background="#d9d9da")
    # root.config(background="#c9f1ed")
    # root.config(background="#9eedfa")


def render_clock(root):
    def time_updater():
        label_date.configure(text="{}".format(time.strftime('%b  %d')))
        label_time.configure(text="{}".format(time.strftime('%I:%M:%S  %p')))
        time_frame.after(1000, time_updater)

    # Global time Frame
    time_frame = Frame(root, background='#c4d1de')
    time_frame.pack(side=TOP, expand=1, anchor=N)
    # Date (some other nice colors: '#003c68', '#08254d', '#48372d')
    label_date = Label(time_frame, text="{}".format(time.strftime('%b  %d')), font=('tacoma', 20), bg='#48372d',
                       fg='white')
    # label_date = Label(time_frame, text="{}".format(time.strftime('%b  %-d')), bg="#eee", font=('times', 20, 'bold'))
    label_date.pack(side=LEFT, ipadx=3, padx=(20, 10), pady=20, ipady=3)
    # Time
    label_time = Label(time_frame, text="{}".format(time.strftime('%I:%M:%S  %p')), font=('tacoma', 20),
                       bg='#48372d', fg='white')
    # label_time = Label(time_frame, text="{}".format(time.strftime('%-I:%-M:%-S  %p')), bg="#eee",
    # font=('times', 20, 'bold'))
    label_time.pack(side=LEFT, ipadx=3, pady=20, ipady=3, padx=(0, 20))

    time_updater()


def render_options(root):
    # Function to store information and reserve the ticket
    def reserve(*args):
        # Remove errorbox in case of any change
        error_flag.set(False)
        # When reserve button is pressed ("reserve var" value = true)
        if reserve_var.get() == True:
            # Error check
            error_check()

            # Single ticket reserve and no error
            if tour.get() == False and error_flag.get() == False:
                # Store data in dictionary to be committed to database (Note: This operation has to be done
                # before cleaning up entries, so we don't lose data)
                to_be_committed["going_ticket"] = {"id": entry_flight_id.get(), "origin": entry_origin.get(),
                                                   "destination": entry_destination.get(),
                                                   "airline": entry_airline.get(), "plane": entry_airplane.get()}
                # ERROR Here we should not do the commit since, the data for form which is going to be
                # stored in db is not yet received
            elif error_flag.get() == False:
                global round_tour
                # First round of execution (for going ticket)
                if round_tour == False:

                    # Change "clear" button functionality (text, and callback func)
                    button_clear.config(text="Back", command=back_btn_handler)
                    # Change "Next" button to "Reserve"
                    button_reserve.config(text="Reserve")

                    # Store data in dictionary to be committed to database (Note: This operation has to be done
                    # before cleaning up entries, so we don't lose data)
                    # going ticket
                    to_be_committed["going_ticket"] = {"id": entry_flight_id.get(), "origin": entry_origin.get(),
                                                       "destination": entry_destination.get(),
                                                       "airline": entry_airline.get(), "plane": entry_airplane.get()}

                    # Config origin and destination entries, and kill their listbox
                    src = entry_origin.get()
                    dst = entry_destination.get()
                    entry_origin.var.set(dst)
                    entry_destination.var.set(src)
                    entry_origin.config(state=DISABLED, disabledforeground="#373737")
                    entry_destination.config(state=DISABLED, disabledforeground="#373737")
                    entry_origin.listbox.destroy()
                    entry_origin.listboxUp = False
                    entry_destination.listbox.destroy()
                    entry_destination.listboxUp = False

                    # Clear all entries, but the two above ("reserve var" value = true)
                    entry_flight_id.cleaner()
                    entry_airline.cleaner()
                    entry_airplane.cleaner()

                    # It flags the first round of execution so next time it will fall to second round (other condition)
                    round_tour = True

                # Second round of execution (for return ticket)
                else:
                    # Store data in dictionary to be committed to database (Note: This operation has to be done
                    # before any clean-up, so we don't lose data)
                    # Return ticket
                    to_be_committed["return_ticket"] = {"id": entry_flight_id.get(), "origin": entry_origin.get(),
                                                        "destination": entry_destination.get(),
                                                        "airline": entry_airline.get(), "plane": entry_airplane.get()}

        # "entry" clean up, if Back button is pressed.
        elif round_tour == True:
            # Restoring state
            entry_origin.config(state=NORMAL)
            entry_destination.config(state=NORMAL)
            # Cleaning up and restoring previous entries
            call_all_clean_methods()
            entry_flight_id.set_value(to_be_committed["going_ticket"]["id"])
            entry_airline.set_value(to_be_committed["going_ticket"]["airline"])
            entry_airplane.set_value(to_be_committed["going_ticket"]["plane"])

            # Clean up db dictionary
            to_be_committed.clear()

            # It undoes first round of reserve execution
            round_tour = False

    # Function to check for errors.
    def error_check(*args):
        global error_type
        # "red highlight" empty entries
        if entry_airline.get() == '':
            error_type = 1
            entry_airline.config(highlightbackground="red")
        if entry_destination.get() == '':
            error_type = 1
            entry_destination.config(highlightbackground="red")
        if entry_airplane.get() == '':
            error_type = 1
            entry_airplane.config(highlightbackground="red")
        if entry_origin.get() == '':
            error_type = 1
            entry_origin.config(highlightbackground="red")
        if entry_flight_id.get() == '':
            error_type = 1
            entry_flight_id.config(highlightbackground="red")
        # If no errors encountered so far, begin the loop. (This is mainly to prevent infinite recursion.)
        if error_type != 0:
            error_flag.set(True)
        else:
            if not [record for record in flight_records if record[6] == entry_flight_id.get()]:
                error_type = 1
                error_flag.set(True)

    # Function to call all entries clean methods
    def call_all_clean_methods(*args):
        entry_flight_id.cleaner()
        entry_origin.cleaner()
        entry_destination.cleaner()
        entry_airline.cleaner()
        entry_airplane.cleaner()

    # Function to set price, and populate all entries immediately after flight id is entered or selected.
    def price_set(listbox=False):
        flight_id = entry_flight_id.get()
        # Remove "PriceTag" When "clear" button pressed by passing a negative value
        if flight_id == '':
            label_price.config(text='')
        elif [record for record in flight_records if record[6] == str(flight_id)]:
            # This checks and forms a dict with records which id matches, passed id which is one since
            # id for records is a primary key hens unique, thus we have one record which is index 0.
            f_id = [record for record in flight_records if record[6] == str(flight_id)][0]
            label_price.config(text="{} $".format(f_id[5]))
            # If the func is called from within "changed" method which launches listbox, then kill it
            # if listbox:
            #     entry_flight_id.listbox.destroy()
            #     entry_flight_id.listboxUp = False
            # When user is entered "flight id", it makes sense to autofill all other entries.
            if f_id:
                date, src, dst, airline, plane, price, id = f_id
                entry_origin.set_value(src)
                entry_destination.set_value(dst)
                entry_airline.set_value(airline)
                entry_airplane.set_value(plane)

    # "Tour" observer
    def options_tour_handler(*args):
        if tour.get() == True:
            # Change "reserve" button to "next"
            button_reserve.config(text="Next")
        else:
            # Change "Next" button to "Reserve"
            button_reserve.config(text="Reserve")

    def back_btn_handler():
        # Set "back" button configs back to "clear"
        button_clear.config(text="Clear", command=call_all_clean_methods)
        # Change "Next" button to "Reserve"
        button_reserve.config(text="Next")

        reserve_var.set(False)

    # Handler func called by "reserve" btn, (intern it triggers, reserve boolVar)
    def reserve_handler():
        reserve_var.set(True)


    # Set the "tour" tk var trigger to execute call_all_clean_methods func
    global_cleaner.trace_add('write', call_all_clean_methods)
    # Set the "tour" tk var trigger to execute handler
    tour.trace_add("write", options_tour_handler)
    # Set trigger to launch handler when "reserve" button pressed
    reserve_var.trace_add('write', reserve)

    # Frame to hold everything else
    option_frame = Frame(root, highlightbackground="green", highlightthickness=1, bg="lightgrey")
    option_frame.pack(padx=20, pady=20, ipadx=20, expand=2)

    # "Flight ID"
    label_flight_id = Label(option_frame, text="Flight ID:   #")
    label_flight_id.grid(row=1, column=0, padx=(40, 5), pady=(20, 20), sticky=W)
    entry_flight_id = AutocompleteEntry(root, set(record[6] for record in flight_records), option_frame, entry_for=6,
                                        set_focus=True, listboxLength=6, width=32)
    entry_flight_id.set_priceTag_method_addr(price_set)
    entry_flight_id.grid(row=1, column=1, sticky=W)

    # Price Tag
    label_price = Label(option_frame, fg="red", font=24)
    label_price.grid(row=1, column=3, sticky=E, padx=(80, 20))
    # Reserve button
    button_reserve = Button(option_frame, text="Reserve", command=reserve_handler, bg='#567', fg='White', width=6)
    button_reserve.grid(row=1, column=4, padx=(40, 20), pady=(20, 20), sticky='w')
    # Clear button
    button_clear = Button(option_frame, text="Clear", command=call_all_clean_methods, bg='#567', fg='White', width=6)
    button_clear.grid(row=1, column=4, padx=(20, 40), pady=(20, 20), sticky='e')

    # "Origin"
    label_origin = Label(option_frame, text="Origin:")
    label_origin.grid(row=2, column=0, padx=(40, 20), pady=(20, 20), sticky=W)
    entry_origin = AutocompleteEntry(root, set(record[1] for record in flight_records), option_frame, entry_for=1,
                                     listboxLength=6, width=32)
    entry_origin.grid(row=2, column=1, sticky=W)

    # "Destination"
    label_destination = Label(option_frame, text="Destination:")
    label_destination.grid(row=2, column=3, padx=(80, 20), pady=(20, 20), sticky=E)
    entry_destination = AutocompleteEntry(root, set(record[2] for record in flight_records), option_frame, entry_for=2,
                                          listboxLength=6, width=32)
    entry_destination.grid(row=2, column=4, sticky=E)

    # "Airline"
    label_airline = Label(option_frame, text="Airline:")
    label_airline.grid(row=3, column=0, padx=(40, 20), pady=(20, 20), sticky=W)
    entry_airline = AutocompleteEntry(root, set(record[3] for record in flight_records), option_frame, entry_for=3,
                                      listboxLength=6, width=32)
    entry_airline.grid(row=3, column=1, sticky=W)

    # "Airplane"
    label_airplane = Label(option_frame, text="Airplane:")
    label_airplane.grid(row=3, column=3, padx=(80, 20), pady=(20, 0))
    entry_airplane = AutocompleteEntry(root, set(record[4] for record in flight_records), option_frame, entry_for=4,
                                       listboxLength=6, width=32)
    entry_airplane.grid(row=3, column=4)

    return entry_flight_id, entry_origin, entry_destination, entry_airline, entry_airplane


def render_form(root):
    # "reserve" handler
    def reserve(*args):
        if reserve_var.get() == True:
            # Error check
            error_check()
            # In tour mode, reservation in progress, and just in "second round" and without errors.
            if round_tour == True and error_flag.get() == False:
                # Disable buttons
                entry_name.config(state=DISABLED, disabledforeground="#373737")
                entry_ssn.config(state=DISABLED, disabledforeground="#373737")
                entry_age.config(state=DISABLED, disabledforeground="#373737")
                # Store data in dictionary to be committed to database (Note: This operation has to be done
                # before any clean-up, so we don't lose data)
                # Tour info
                to_be_committed["tour"] = {"num of passengers": entry_age.get(), "manager": entry_name.get(),
                                           "company": entry_ssn.get()}
                ###########################
                upload_db()
                ###########################
            # Passenger mode and without errors
            elif error_flag.get() == False:
                to_be_committed["passenger"] = {"age": entry_age.get(), "name": entry_name.get(),
                                                "ssn": entry_ssn.get()}
                ###########################
                upload_db()
                ###########################

        else:  # when reserve_var.get() == False
            # Execute only in "tour" mode
            # if tour.get() == True: # I removed the control condition, because otherwise never happens
            # Execute only when Reservation is not in progress (the trigerring var is set to false)
            if reserve_var.get() == False:
                entry_name.config(state=NORMAL)
                entry_ssn.config(state=NORMAL)
                entry_age.config(state=NORMAL)

    # Function to check for errors.
    def error_check(*args):
        global error_type
        # "red highlight" empty entries
        if entry_name.get() == '':
            error_type = 1
            entry_name.config(highlightbackground="red")
        if entry_ssn.get() == '':
            error_type = 1
            entry_ssn.config(highlightbackground="red")
        if entry_age.get() == '':
            error_type = 1
            entry_age.config(highlightbackground="red")
        # If no errors encountered so far, begin the loop. (This is mainly to prevent infinite recursion.)
        if error_type != 0:
            error_flag.set(True)
        else:
            if tour.get() == False:
                # Age has to be a number
                try:
                    int(entry_age.get())
                except:
                    error_type = 3
                    entry_age.config(highlightbackground="red")
                    error_flag.set(True)

                # In tour mode check if ssn is number and 10-digit
                if len(entry_ssn.get()) != 10:  # 10-digit
                    error_type = 6
                    entry_age.config(highlightbackground="red")
                    error_flag.set(True)
                try:  # number check
                    int(entry_ssn.get())
                except:
                    error_type = 5
                    entry_age.config(highlightbackground="red")
                    error_flag.set(True)
            else:
                # Number of booking has to be a number
                try:
                    int(entry_age.get())
                except:
                    error_type = 7
                    entry_age.config(highlightbackground="red")
                    error_flag.set(True)

    # Trigger funcs to Switch passenger panel
    def if_true_then_false():
        on_change_trigger_func()
        if tour.get() == True:
            tour.set(False)

    # Trigger funcs to Switch tour panel
    def if_false_then_true():
        on_change_trigger_func()
        if tour.get() == False:
            tour.set(True)

    # "Tour" observer
    def form_tour_handler(*args):
        if tour.get() == True:
            # Change labels
            label_name.config(text="Manager:")
            label_ssn.config(text="Company:")
            label_age.config(text="Num Tickets:")
            # Clear entries
            entry_name.delete(0, END)
            entry_ssn.delete(0, END)
            entry_age.delete(0, END)
        else:
            # Change labels
            label_name.config(text="Full Name:")
            label_ssn.config(text="SSN:")
            label_age.config(text="Age:")
            # Clear entries
            entry_name.delete(0, END)
            entry_ssn.delete(0, END)
            entry_age.delete(0, END)

    # Mapped to a global tkinter boolvar for cleaning the page when closing the page (restoring initial form)
    def local_cleaner(*args):
        # Clear entries
        entry_name.delete(0, END)
        entry_ssn.delete(0, END)
        entry_age.delete(0, END)


    # Set the "tour" tk var trigger to execute call_all_clean_methods func
    global_cleaner.trace_add('write', local_cleaner)
    # Set the "tour" tk var trigger to execute handler
    tour.trace_add("write", form_tour_handler)

    # Set trigger to launch handler when "reserve" button pressed
    reserve_var.trace_add('write', reserve)

    form_frame = Frame(root, highlightbackground="green", highlightthickness=1, bg="lightgrey")
    form_frame.pack(padx=20, ipadx=20, ipady=20)

    # Full name / Manager
    label_name = Label(form_frame, text="Full Name:")
    label_name.grid(row=0, column=0, padx=(20, 0), pady=20)
    entry_name = Entry(form_frame, width=25)
    entry_name.grid(row=0, column=1, padx=20)
    # Even for overriding border color of entries in case of any change (when on error it has turned to red)
    entry_name.bind("<KeyPress>", lambda *args: entry_name.config(highlightbackground='lightgrey'))


    # Reservation type
    label_reserve_type = Label(form_frame, text="Reserve panel:", font=2)
    label_reserve_type.grid(row=0, column=2, padx=(20, 0))

    # Radio Button to switch between tour/passenger reserving panel
    radio_btn_pass = Radiobutton(form_frame, value=0, text="Tour", command=if_false_then_true, font=8)
    radio_btn_tour = Radiobutton(form_frame, value=1, text="Passenger", command=if_true_then_false, font=8)
    radio_btn_tour.grid(row=0, column=3, sticky=W, padx=(10, 0))
    radio_btn_pass.grid(row=0, column=3, sticky=E, padx=(0, 10))

    # SSN / Company
    label_ssn = Label(form_frame, text="SSN:")
    label_ssn.grid(row=1, column=0, padx=(20, 0))
    entry_ssn = Entry(form_frame, width=25)
    entry_ssn.grid(row=1, column=1, padx=20)
    # Even for overriding border color of entries in case of any change (when on error it has turned to red)
    entry_ssn.bind("<KeyPress>", lambda *args: entry_ssn.config(highlightbackground='lightgrey'))

    # Age / Number tickets
    label_age = Label(form_frame, text="Age:")
    label_age.grid(row=1, column=2, padx=20, pady=(10, 0))
    entry_age = Entry(form_frame, width=25)
    entry_age.grid(row=1, column=3, padx=20)
    entry_age.bind("<KeyPress>", lambda *args: entry_age.config(highlightbackground='lightgrey'))


def render_table(root):
    # Frame to hold table
    table_frame = Frame(root)
    table_frame.pack(side=BOTTOM, fill=X, expand=1, anchor=S)
    # table_frame.grid(row=0, column=1, sticky=S)

    ################# Table code using tkinter's "treeview" module
    # Instantiation and coordinate "table" object
    tree = SmartTable(table_frame)
    tree.pack(fill=BOTH, side=LEFT, expand=2)
    # Scroll Bar
    table_sb = Scrollbar(table_frame, orient=VERTICAL)
    table_sb.pack(side=RIGHT, fill=Y)
    tree.config(yscrollcommand=table_sb.set)
    table_sb.config(command=tree.yview)

    # Return object address to use for autocompletion capability with entry
    return tree


def render_error(root):
    def error_handle(*args):
        global error_type
        if error_flag.get() == True:
            label.config(text=err_opcodes[error_type])
        else:
            label.config(text='', background="#c4d1de")
            # Since independent error check is done on every attempt, and on error check handlers inside main funcs
            # value of this variable is based on considering on existence of errors, so I need to clear it out
            error_type = 0

    # Make and pack error frame
    error_frame = Frame(root)
    error_frame.pack()
    # Make and pack Label
    label = Label(error_frame, bg="white", fg="red", font=20)
    label.pack()
    """Error opcodes:"""
    err_opcodes = {
        1: "* Fill up all the required fields",
        2: "* No flight matching your request is registered",
        3: "* Age field has to be a number",
        4: "* Database error occurred",
        5: "* SSN has to be a number",
        6: "* SSN has to be 10-digit",
        7: "* Number of booking field has to be a number",
    }

    error_flag.trace_add('write', error_handle)


def upload_db():
    try:
        connection = sqlite3.connect("Airport.db")
        cursor = connection.cursor()

        # If we're reserving in tour mode (ie, multiple tickets)
        if tour.get() == True:
            company = to_be_committed["tour"]["company"]
            manager = to_be_committed["tour"]["manager"]
            num_booking = to_be_committed["tour"]["num of passengers"]
            going_flight_id = to_be_committed["going_ticket"]["id"]
            return_flight_id = to_be_committed["return_ticket"]["id"]
            origin = to_be_committed["going_ticket"]["origin"]
            destination = to_be_committed["return_ticket"]["origin"]
            fake_record = 0
            tour_id = ''.join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=10))
            sql_query = """INSERT INTO tour VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')""".format\
                (tour_id, manager, company, origin, destination, num_booking, going_flight_id, return_flight_id, fake_record)
        # If we are reserving in passenger mode (ie. single ticket)
        else:

            name = to_be_committed["passenger"]["name"]
            age = to_be_committed["passenger"]["age"]
            ssn = to_be_committed["passenger"]["ssn"]
            origin = to_be_committed["going_ticket"]["origin"]
            destination = to_be_committed["going_ticket"]["destination"]
            passenger_id = ''.join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=10))
            country = "iran"
            fake_record = 0
            now = datetime.date.today().strftime('%Y-%m-%d')
            flight_id = to_be_committed["going_ticket"]["id"]
            sql_query = """INSERT INTO Passenger VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')""".format\
                (passenger_id, flight_id, ssn, country, fake_record, age, now, name)

        cursor.execute(sql_query)
        connection.commit()
        cursor.close()

    except sqlite3.Error as error:
        print("Error while working with SQLite", error)
        # Invoke error handling procedure
        global error_type
        error_type = 4
        error_flag.set(True)
    # This is when "try" statement successfully executed
    else:
        # After successful execution clean out the db for future uses
        global_cleaner.set(False)
        par.deiconify()
        # root.destroy()
        root.withdraw()
    finally:
        if connection:
            print("Total Rows affected since the database connection was opened: ", connection.total_changes)
            connection.close()
            print("sqlite connection is closed")


def run(parent=par):
    def exit_func():
        # When closing the page, clean out all entries
        global_cleaner.set(False)

        par.deiconify()
        root.withdraw()
        # root.destroy()

    global root
    # Instantiate root window
    root = Toplevel(par)
    # Load dataset
    load_db()
    # Render page by executing corresponding functions
    render_root(root)
    render_clock(root)
    render_form(root)
    entry_flight_id, entry_origin, entry_destination, entry_airline, entry_airplane = render_options(root)
    smart_table = render_table(root)
    render_error(root)

    # Exchange object addresses, required for implementing auto filtering functionality
    entry_flight_id.set_table_func_addr(smart_table)
    entry_origin.set_table_func_addr(smart_table)
    entry_destination.set_table_func_addr(smart_table)
    entry_airline.set_table_func_addr(smart_table)
    entry_airplane.set_table_func_addr(smart_table)
    smart_table.set_options_func_addr(id=entry_flight_id, src=entry_origin,
                                      dst=entry_destination, airline=entry_airline, plane=entry_airplane)

    # Define procedure to execute when closing window
    root.protocol('WM_DELETE_WINDOW', exit_func)


if __name__ == "__main__":
    run()
