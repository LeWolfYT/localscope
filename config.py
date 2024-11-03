import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkf
import tkinter.messagebox as tkm
#import tkinter.colorchooser as tkc

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
add_var("units", "e")
add_var("locale", "en-US")
add_var("sysfont", True)
add_var("font", "Arial")
add_var("bold", True)
add_var("performance", False)
add_var("sound", True)
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
add_var("useredmusic", False)
add_var("redmusic", "")
add_var("manualmusic", False)
add_var("scaled", False)
add_var("smoothscale", False)
add_var("size", (1920, 1080))
add_var("graphicalwidth", 840)
add_var("background_image_use", False)
add_var("background", "")
add_var("backgroundred", "")
add_var("image_replace", {})
add_var("color_replace", {})

title = ttk.Label(root, text=name)
title.place(x=5, y=5)

def toggleit(k): #, plus=None, *args, **kwargs):
    new = not allvars[k]
    allvars[k] = not allvars[k]
    #if plus != None:
    #    plus(new, *args, **kwargs)

notes = ttk.Notebook(root)
notes.place(x=5, y=35, relwidth=1, width=-10, relheight=1, height=-55)

general = ttk.Frame(notes)
audio = ttk.Frame(notes)
video = ttk.Frame(notes)
perform = ttk.Frame(notes)
imag = ttk.Frame(notes)
partner = ttk.Frame(notes)

scaleframe = ttk.Frame(video)

audframed = ttk.Frame(audio)
audframep = ttk.Frame(audio)

menuu = tk.Menu(root)
root.option_add("*tearOff", tk.FALSE)
root["menu"] = menuu

notes.add(general, text="General")
notes.add(audio, text="Audio")
notes.add(video, text="Video")
notes.add(perform, text="Performance")
notes.add(imag, text="Images")
notes.add(partner, text="Branding")

def savei(k, v, *args):
    allvars[k] = v

perf = ttk.Checkbutton(general, text="Performance Mode", variable=tk.IntVar(value=allvars["performance"]), command=lambda : toggleit("performance"))
#perf = ttk.Checkbutton(general, text="Performance Mode", command=lambda e : savei("performance", e))
perf.place(x=0, y=0)
savedmusicmode = tk.StringVar(value=allvars["musicmode"])

soun = ttk.Checkbutton(audio, text="Play sound", variable=tk.IntVar(value=allvars["sound"]), command=lambda : toggleit("sound"))

def selectpath(k):
    pa = tkf.askdirectory(initialdir=(allvars[k] if allvars[k] else None))
    if pa != "":
        allvars[k] = pa

def selectfil(k, fl):
    pa = tkf.askopenfilename(initialfile=(allvars[k] if allvars[k] else None), filetypes=fl)
    if pa != "":
        allvars[k] = pa

dpath = ttk.Button(audframed, text=f"Set Daytime Music{'' if allvars['daytheme'] else ' (UNSET)'}", command=lambda : selectfil("daytheme", [("Audio Files", ".mp3 .wav .ogg .xm .mod .it .s3m .flac")]))
npath = ttk.Button(audframed, text=f"Set Nightime Music{'' if allvars['nighttheme'] else ' (UNSET)'}", command=lambda : selectfil("nighttheme", [("Audio Files", ".mp3 .wav .ogg .xm .mod .it .s3m .flac")]))
mpath = ttk.Button(audframep, text=f"Music Directory{'' if allvars['musicdir'] else ' (UNSET)'}", command=lambda : selectpath("musicdir"))
dpath.place(x=0, y=0)
npath.place(x=0, y=30)
mpath.place(x=0, y=20)

def domusicmodethings(e):
    savei("musicmode", e)
    if e == "daytime":
        audframed.place(x=0, y=60, relwidth=1, height=70)
        audframep.place_forget()
    else:
        audframep.place(x=0, y=60, relwidth=1, height=70)
        audframed.place_forget()
musicmode = ttk.OptionMenu(audio, savedmusicmode, savedmusicmode.get(), "daytime", "playlist", command=lambda e : domusicmodethings(e))
domusicmodethings(allvars["musicmode"])
musiclabel = ttk.Label(audio, text="Music Mode")
soun.place(x=0, y=0)
musicmode.place(x=0, y=30)
musiclabel.place(x=90, y=34)

redtoggle = ttk.Checkbutton(audio, text="Custom Red Mode Music", variable=tk.IntVar(value=allvars["useredmusic"]), command=lambda : toggleit("useredmusic"))
redtoggle.place(x=0, y=140)
redpath = ttk.Button(audio, text=f"Red Mode Music Path{'' if allvars['redmusic'] else ' (UNSET)'}", command=lambda : selectfil("redmusic", [("Audio Files", ".mp3 .wav .ogg .xm .mod .it .s3m .flac")]))
redpath.place(x=0, y=170)

scaled = ttk.Checkbutton(video, text="Scaled?", variable=tk.IntVar(value=allvars["scaled"]), command=lambda : toggleit("scaled"))
scaled.place(x=0, y=0)

def spinit(k, v, i):
    if type(allvars[k]) == tuple:
        allvars[k] = list(allvars[k])
    allvars[k][i] = v

scalex = ttk.Spinbox(video, from_=0, to=99999999, command=lambda : spinit("size", scalex.get(), 0), validate="all")
scaley = ttk.Spinbox(video, from_=0, to=99999999, command=lambda : spinit("size", scaley.get(), 1), validate="all")
scalel = ttk.Label(video, text="Scale Size")
scalex.set(allvars["size"][0])
scaley.set(allvars["size"][1])
scalel.place(x=0, y=30)
scalex.place(x=0, y=60)
scaley.place(x=220, y=60)
scaled = ttk.Checkbutton(perform, text="Use smooth scaling", variable=tk.IntVar(value=allvars["smoothscale"]), command=lambda : toggleit("smoothscale"))
scaled.place(x=0, y=0)

def check_save():
    warnings = []
    if allvars["musicmode"] == "playlist":
        if allvars["musicdir"] == "":
            warnings.append("The music mode is set to \"Playlist\" but no music directory was specified.")
    else:
        if allvars["daytheme"] == "" and allvars["nighttheme"] == "":
            warnings.append("The music mode is set to \"Daytime\", but neither themes were specified.")
        elif allvars["daytheme"] == "":
            warnings.append("The music mode is set to \"Daytime\", but no daytime theme was specified.")
        elif allvars["nighttheme"] == "":
            warnings.append("The music mode is set to \"Daytime\", but no nighttime theme was specified.")
    if allvars["useredmusic"]:
        if allvars["redmusic"] == "":
            warnings.append("Red mode music is enabled, but no theme was specified for it.")
    return warnings

def saveit():
    res = check_save()
    if res != []:
        msgg = ""
        for i, w in enumerate(res):
            ww = w
            if i == 0:
                msgg += w
            else:
                ww[0] = ww[0].lower()
                msgg += ("Also, " + ww)
        tkm.askyesno("Warning!", msgg)
    buffer = ""
    for var in allvars.keys():
        buffer += f'{var}={allvars[var].__repr__()}'
        buffer += "\n"
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vars.py"), "w") as ff:
        ff.write(buffer)
save = ttk.Button(root, text="Save", command=saveit)
save.place(rely=1, x=5, anchor="sw", y=-5)

root.mainloop()