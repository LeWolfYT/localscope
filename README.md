# My Weather Station

Do you like the Wii Forecast Channel? Maybe The Weather Channel's older WeatherStar units? Maybe you just want a fun way of checking the weather? Look no further! (#TODO: Remind me to add some more info here.)

## Setup

While setting up the app, you'll need to create a `vars.py` file in the same folder as the main program. An example is demonstrated below.
```python
weatheraddr = "http://wttr.in/?format=j2" #not used usually
coords = "lat,long" #no spaces
forcecoords = True #please use unless you are using musicmode="daytime". wttr.in is outdated
station = "KPIT"
timezone = "EST"

sysfont = True #will use a system font if true, ttf if false
font = "Arial" #font name or file path

#music
sound = True #will play sound
musicmode = "playlist" #playlist or daytime
daytheme = "/path/to/day/music.mp3"
nighttheme = "/these/only/play/in/musicmode/daytime.mp3"
musicdir = "/Users/pj/Downloads/weathermusic"
manualmusic = False #in playlist mode this will make songs loop until you press minus

musicdir = "/this/only/plays/in/playlist/mode/"

ads = ["example ad 1", "example ad 2", "example ad 3", "example ad 4", "example ad 5"]
adcrawltime = 10 #in seconds

partnered = True #you can add your logo to the 7-day forecast
logo = "/my/cool/logo.png"

graphicalwidth = 840
#change depending on image height. keep in mind that you have around 640px of vertical space and 1000px of horizontal space
#for the contiguous usa, 840 works fine
```
Right now, you can use this template as vars.py, changing the paths if needed.

## Contributing

This project is in **very active** development and any and all contributions are welcome! I'll be making it a goal to label some of my spaghetti code to make contributing easier.

## Versions

There are currently two versions of the app. Version 1 is found in main.py, and ws4k.py is version 2. Version 1 is the main version, and version 2 is where I experiment with things a bit more. Please use version 1.
Recently, we've added a "Version 1.1" of sorts in the form of the LocalScan program (scan.py). If you want to live stream, use that!
