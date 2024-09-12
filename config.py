import tkinter as tk
import tkinter.ttk as ttk
import os
try:
    import vars as varr
except ImportError:
    varr = {}
root = tk.Tk()
root.geometry("640x480")
name = "LocalScope Configuration Tool v1.0"
root.title(name)

allvars = {}
def add_var(varname, d):
    allvars[varname] = getattr(varr, varname, d)
add_var("weatheraddr", "http://wttr.in/?format=j2")
add_var("coords", "40.7128,-74.006")
add_var("forcecoords", "True")
add_var("station", "KJFK")
add_var("sysfont", True)
add_var("font", "Arial")
add_var("bold", True)
add_var("performance", False)
add_var("musicmode", "playlist")
add_var("ads", [])
add_var("adcrawltime", 10)
add_var("sector", "conus")
add_var("timezone", "EST")
add_var("warningsector", "conus")
add_var("hurricanesector", "pac")
add_var("partnered", False)
add_var("logo", "")
add_var("daytheme", "")
add_var("nighttheme", "")
add_var("musicdir", "")
add_var("manualmusic", False)
add_var("scaled", False)
add_var("smoothscale", False)
add_var("size", (1920, 1080))
add_var("graphicalwidth", 840)
add_var("background_image_use", False)
add_var("background", "")
add_var("backgroundred", "")



title = ttk.Label(root, text=name)
title.place(x=5, y=5)

def toggleit():
    allvars["performance"] = not allvars["performance"]

notes = ttk.Notebook(root)
notes.place(x=5, y=35, relwidth=1, width=-10, relheight=1, height=-55)

general = ttk.Frame(root)
video = ttk.Frame(root)
audio = ttk.Frame(root)

notes.add(general, text="General")
notes.add(audio, text="Audio")
notes.add(video, text="Video")

perf = ttk.Checkbutton(general, text="Performance Mode", variable=tk.IntVar(value=allvars["performance"]), command=toggleit)
perf.place(x=0, y=0)

def saveit():
    buffer = ""
    for var in allvars.keys():
        buffer += f'{var}={allvars[var].__repr__()}'
        buffer += "\n"
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vars.py"), "w") as ff:
        ff.write(buffer)
save = ttk.Button(root, text="Save", command=saveit)
save.place(rely=1, x=5, anchor="sw", y=-5)

root.mainloop()