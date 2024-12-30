# LocalScope

Do you like the Wii Forecast Channel? Maybe The Weather Channel's older WeatherStar units? Maybe you just want a fun way of checking the weather? Look no further!

## Important Note

Don't use any plugins or themes from untrustworthy sources. Because they have programming support, they can be used to execute arbitrary code on your computer. Only use plugins and themes that come bundled or reviewed ones from the upcoming LocalScope Depot unless you know what you're doing.

## What's new in The Everything Update?

- Plugin support
- Themes can now have custom code
- Icon pack support
- Text-based hourly forecast
- A new health section
  - UV index
  - Air quality
  - Pollen count
- Support for reading from online streams
- Built-in streaming support
- Various bug fixes and improvements
- A new compact mode
- Custom screen width settings
- Improved performance (thanks to caching and other optimizations)

Note: Performance mode is currently unstable and may have various issues with drawing the screen. Use with caution.
Note 2: Update your language files, since many new strings have been added.

## Bundled Plugins

- Countdown (counts down to christmas)
- example slide (adds an example slide to the rotation)
- example ticker (adds an example ticker text)
- snow (adds falling snow to the screen)

## Bundled Themes

Note: The only fully complete theme is Metallic. Intelli currently only affects the infobar and the ticker.

- default (the default theme, not in the folder though since it's just what you get without a theme)
- Jerald (by SSPXWR, flat theme with orange highlights)
- something to grab peoples attention (idea by lexio, programmed by LeWolfYT, it's a surprise)
- Metallic (by LeWolfYT, more realistic theme with metallic everything)
- Intelli (by LeWolfYT, a theme based on the first graphics package for the original IntelliStar)
- HDS (by LeWolfYT, a theme based on WeatherHDS. go check the actual WeatherHDS out, it's cool)
- 4000 (by LeWolfYT, a theme based on the WeatherSTAR 4000. don't use, it hasn't been fully implemented yet)

## Setup

While setting up the app, you'll need to create a `vars.py` file in the same folder as the main program. An example is demonstrated below.

```py
weatheraddr = "http://wttr.in/?format=j2" #not used usually
coords = "lat,long" #no spaces
forcecoords = True #please use unless you are using musicmode="daytime". wttr.in is outdated
station = "KPIT" #ICAO code of your nearest airport
timezone = "EST"

sysfont = True #will use a system font if true, ttf if false
font = "Arial" #font name or file path

#music
sound = True #will play sound
musicmode = "playlist" #playlist or daytime
daytheme = "/path/to/day/music.mp3"
nighttheme = "/these/only/play/in/musicmode/daytime.mp3"
musicdir = "/path/to/your/music/"
manualmusic = False #in playlist mode this will make songs loop until you press minus

musicdir = "/this/only/plays/in/playlist/mode/"

#leave these blank if you don't want to use them
ads = ["example ad 1", "example ad 2", "example ad 3", "example ad 4", "example ad 5"]
adcrawltime = 10 #in seconds

partnered = True #you can add your logo to the credits
logo = "/my/cool/logo.png"

screenwidth = 1366 #1366 is default, for 4:3 use 1024. height is always 768
compact = False #if true, will use a more compact layout for certain elements. good for if you like square screens
scaled = True #if true, rescales to the size below
smoothscale = True
size = (1920, 1080)

#for background images (set to false if you want to use the gradient image set in your theme)
background_image_use = True
background = "/path/to/img.jpg"
backgroundred = "/path/to/redimg.jpg"

units = "e" #any TWC unit type works here
locale = "en-US" #currently the only officially supported languages are en-US (American English) and de-DE (German). Add your own languages by adding JSON files with the locale name in the lang folder.
apikey = 'KEY GOES HERE'
extendedfamount = 18 #how many days+nights of extended forecast to show. keep this even for best results

#leave these out if you don't want to use them
stream = "https://example.com/stream.ts" #stream URL
writer = "rtmp://example.com/live" #stream output. if you want to use tee muxer, make this an array and we'll do the work for you
audiofile = "/path/to/audio.wav" #audio file for the stream. this gets played in the background on loop, since pygame doesn't support getting the currently playing audio bytes. don't set this if you want no audio
maskcolor = (255, 0, 255) #color to be used as the background for the stream
stretchmode = "stretch" #fit, fill, stretch
#streamheight = 768 #height of the stream, leave out for default
streamy = 0 #y offset

plugins = [] #add plugins here. the plugin name is the folder name of the plugin in the plugins folder
theme = "theme name here, leave blank or omit for default"
iconpack = "icon pack name here, leave blank or omit for default"

miniplayer=False #if true, will add a miniplayer for the stream
miniplayerheight=120 #height of the miniplayer, width is calculated automatically
ldlmode_top = True #if true, will show the infobar in LDL mode
ldlmode_shadow = True #if true, will show shadows in LDL mode

ldlmode_watermark = False #if true, will show a watermark in LDL mode
watermark_path = '/path/to/watermark.png' #path to the watermark image

#these next two can be useful for if you're using custom fixtures that take up one of these slots (like the countdown plugin)
hide_fixture_left = False #if true, will hide the left fixture
hide_fixture_right = False #if true, will hide the right fixture

```

Right now, you can use this template as vars.py, changing the paths and values as needed.

## Segments

Right now, you can press the 1 key to show the normal weather and the 2 key to start overlay mode. Set your chroma key to magenta for it to work. In OBS, a similarity value of 200 works best.

## Keybinds

There are a few keybinds that can be helpful to use. Pressing the E key will export all of the assets used by the program, including gradients generated on-the-fly. The F key will toggle an FPS counter on the top left, in place of the current time.

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

### All colors

`gradient_c` (Background)

`gradient_redc` (Background, red mode)

`topgradient_c` (Infobar)

`topgradienthealth_c` (Infobar, health section)

`topgradientcustom_c` (Infobar, custom slides)

`topgradientred_c` (Infobar, red mode)

`bottomgradient_c` (Ticker)

`bottomgradient_redc` (Ticker, red mode)

`chartbg_c` (Hourly Graph chart)

`hourlybg_c` (Hourly Forecast panel)

`weekbg_c` (Extended Forecast chart, normal version)

`weekbg_darkc` (Extended Forecast chart, night)

`weekbg_endc` (Extended Forecast chart, weekend)

`weekbg_dendc` (Extended Forecast chart, weekend night)

### Gradients (by geometry)

(Screen width)x64 (default 1366x64)

`topgradient` (Infobar)

`topgradienthealth` (Infobar, health section)

`topgradientcustom` (Infobar, custom slides)

`topgradientred` (Infobar, red mode)

`bottomgradient` (Ticker)

`bottomgradientred` (Ticker, red mode)

140x276

`weekbgc` (Extended Forecast chart, normal version)

`weekbgnc` (Extended Forecast chart, night)

`weekbgwc` (Extended Forecast chart, weekend)

`weekbgwnc` (Extended Forecast chart, weekend night)

(Screen width - 30)x556 (default 1336x556)

`graphbg` (Hourly Graph chart)

(Screen width - 30)x92 (default 1336x92)

`hourlybg` (Hourly Forecast panel)

### How to add

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
