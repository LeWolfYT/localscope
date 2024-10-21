# LocalScope

Do you like the Wii Forecast Channel? Maybe The Weather Channel's older WeatherStar units? Maybe you just want a fun way of checking the weather? Look no further! (#TODO: Remind me to add some more info here.)

## Setup

While setting up the app, you'll need to create a `vars.py` file in the same folder as the main program. An example is demonstrated below.
```
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

scaled = True #if true, rescales to the size below
smoothscale = True
size = (1920, 1080)

graphicalwidth = 840
graphicalscale = 0.9
#change depending on image height. keep in mind that you have around 640px of vertical space and 1000px of horizontal space
#for the contiguous usa, 840 works fine

#for background images (set to false for gradient)
background_image_use = True
background = "/path/to/img.jpg"
backgroundred = "/path/to/redimg.jpg"
```
Right now, you can use this template as vars.py, changing the paths if needed.

## Segments

Right now, you can press the 1 key to show the normal weather and the 2 key to start overlay mode. Set your chroma key to magenta for it to work. In OBS, a similarity value of 200 works best.

## Contributing

This project is in **very active** development and any and all contributions are welcome! I'll be making it a goal to label some of my spaghetti code to make contributing easier.

## Versions

There are currently two versions of the app. Version 1 is found in main.py, and ws4k.py is version 2. Version 1 is the main version, and version 2 is where I experiment with things a bit more. Please use version 1.
A little while ago, we added a "Version 1.1" of sorts in the form of the LocalScope program (scan.py). If you want to live stream, use that! Also check out the official live stream at live.mistweather.com!

## Custom Colors and Images

In vars.py, you are able to set images to be used in place of certain gradients, as well as different colors for the gradients.
The information on image sizes and color formats will be laid out here.
Note that images WILL NOT be scaled automatically, unlike custom backgrounds.

Color format:

```py
color_c = ((r1, g1, b1), (r2, g2, b2))
```

(This format goes from either top to bottom or left to right)

All colors:

`gradient_c` (Background)

`gradient_redc` (Background, red mode)

`topgradient_c` (Information Panel)

`topgradientred_c` (Information Panel, red mode)

`bottomgradient_c` (Ticker)

`bottomgradient_redc` (Ticker, red mode)

`chartbg_c` (Hourly Graph chart)

`weekbg_c` (Extended Forecast chart, normal version)

`weekbg_darkc` (Extended Forecast chart, night)

Gradients (by geometry):

(Screen width)x64 (default 1366x64)

`topgradient`

`topgradientred`

`bottomgradient`

`bottomgradientred`

140x276

`weekbgc` (Extended Forecast chart, normal version)

`weekbgnc` (Extended Forecast chart, night)

(Screen width - 30)x556 (default 1336x556)

`graphbg` (Hourly Graph chart)

### How to add:

```py
color_replace = {
    "weekbg_c", ((r1, g1, b1), (r2, g2, b2)),
    "weekbg_darkc", ((r3, g3, b3), (r4, g4, b4)),
}
image_replace = {
    "topgradient", "path/to/image.png",
    "bottomgradient", "path/to/image2.png"
}
```

and so on for every replacement.

## A footnote about Ticker/LDL Mode

Currently, custom graphics are broken with this mode. This will be fixed soon.