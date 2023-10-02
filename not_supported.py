import tkinter
from parent import root


def run():
    def on_close():
        window.destroy()
        root.deiconify()

    window = tkinter.Toplevel(root)
    message = """
    SORRY, THIS PANEL IS NOT ADDED YET!
    Currently all the data related to admin, and manager panel is
    committed to database only from "populate_database.py script."   
    Only "PASSENGER PANEL" is supported, currently.
    """
    label = tkinter.Label(window, text=message, font=20, fg="red", bg="lightyellow",)
    label.pack()

    window.geometry("640x400")

    window.protocol("WM_DELETE_WINDOW", on_close)
