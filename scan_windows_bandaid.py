import threading as th
#import multiprocessing as mp
import requests as r
import pygame as pg
import datetime as dt
from io import BytesIO
import isodate as it
import pytz as tz
import vars
import os
import random as rd
import time

sound = getattr(vars, "sound", True)
manualmusic = getattr(vars, "manualmusic", False)
ads = getattr(vars, "ads", ["Place an ad here."])
actime = getattr(vars, "adcrawltime", 4)

debug = False
def debugsleep():
    if debug:
        time.sleep(0.1)
        pg.display.flip()
        pg.event.pump()

#caches
global cache
cache = {}
global textcache
textcache = {}
global textcachecol
textcachecol = {}
global tempcache
global tempcachecol
tempcache = {}
tempcachecol = {}
global crunchcache
crunchcache = {}
global crunchcachecol
crunchcachecol = {}
global bigcrunchcache
bigcrunchcache = {}

global scaled
scaled = getattr(vars, "scaled", False)
global scale
scale = getattr(vars, "size", (1336, 768))
global smoothsc
smoothsc = getattr(vars, "smoothscale", True)

global partnered
partnered = getattr(vars, "partnered", False)
global partnerlogo
partnerlogo = getattr(vars, "logo", None)

rheaders = {
    "User-Agent": "(lewolfyt.github.io, ciblox3+myweatherstation@gmail.com)"
}

assetdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
iconf = os.path.join(assetdir, "icon.bmp")
global logo
logo = pg.image.load(iconf)
pg.display.set_icon(logo)

graphicloc = getattr(vars, "sector", "CONUS").upper()
wgraphicloc = getattr(vars, "warningsector", "CONUS").upper()
graphicwidth = getattr(vars, "graphicalwidth", 840)

#links, no touching these unless you know what you're doing
gtz = getattr(vars, "timezone", "GMT")

#TODO: figure out what n does
gtempurl = f"https://graphical.weather.gov/GraphicalNDFD.php?width={graphicwidth}&timezone={gtz}&sector={graphicloc}&element=t&n=4"
grainurl = f"https://graphical.weather.gov/GraphicalNDFD.php?width={graphicwidth}&timezone={gtz}&sector={graphicloc}&element=pop12&n=4"
warnsurl = f"https://radar.weather.gov/ridge/standard/{wgraphicloc}_0.gif"

#the todo list
#TODO: add a way to organize views
#TODO: add the hourly forecast (graph done)
#TODO: hurricane images
#TODO: make the mouse work better
#TODO: icons to show if the mouse does something

timeformat = "%I:%M %p"
timeformattop = "%I:%M:%S %p"

weatheraddr = getattr(vars, "weatheraddr", "http://wttr.in?format=j2")

musicmode = getattr(vars, "musicmode", "playlist")

playmusic = getattr(vars, "musicdir", False)

def wraptext(text, rect, font):
    rect = pg.Rect(rect)
    y = rect.top
    lineSpacing = -2

    # get the height of the font
    fontHeight = font.size("Tg")[1]
    lines = []

    while text:
        i = 1
        # determine if the row of text will be outside our area
        if y + fontHeight > rect.bottom:
            break

        # determine maximum width of line
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1

        # if we've wrapped the text, then adjust the wrap to the last word      
        if i < len(text): 
            i = text.rfind(" ", 0, i) + 1

        # render the line and blit it to the surface
        
        lines.append(text[:i])

        y += fontHeight + lineSpacing

        # remove the text we just blitted
        text = text[i:]

    return lines

def degrees_to_compass(degrees):
    if degrees == None:
        return "XX"
    """Converts degrees (0-360) to 16-point compass direction."""

    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

    index = round(degrees / 22.5) % 16  # Calculate index, wrap around for 360

    return directions[index]

pg.init()
if not scaled:
    window = pg.display.set_mode((1336, 768), flags=pg.NOFRAME)
else:
    window = pg.Surface((1336, 768))
    final = pg.display.set_mode(scale)
pg.display.set_allow_screensaver(False)
pg.mouse.set_visible(False)

pg.display.set_caption("LocalScan v1.00")

if sound:
    daytheme = pg.mixer.Sound(vars.daytheme)
    nighttheme = pg.mixer.Sound(vars.nighttheme)

def generateGradient(col1, col2, w=1336, h=768, a1=255, a2=255):
    r1, g1, b1 = col1[0], col1[1], col1[2]
    r2, g2, b2 = col2[0], col2[1], col2[2]
    surface = pg.Surface((w, h)).convert_alpha()
    surface.fill((255, 255, 255, 255))
    for i in range(h):
        tr = i/(h-1)
        transpar = pg.Surface((w, 1)).convert_alpha()
        transpar.fill((255, 255, 255, (a1*(1-tr) + a2*tr)))
        pg.draw.line(transpar, ((r1*(1-tr) + r2*tr), (g1*(1-tr) + g2*tr), (b1*(1-tr) + b2*tr)), (0, 0), (w, 0))
        surface.blit(transpar, (0, i), special_flags=pg.BLEND_RGBA_MULT)
    return surface.convert_alpha()

def turnintoashadow(surf: pg.Surface, shadow=127):
    newsurf = pg.Surface((surf.get_width(), surf.get_height())).convert_alpha()
    newsurf.fill((0, 0, 0, 0))
    newsurf.blit(surf, (0, 0))
    black = pg.Surface((surf.get_width(), surf.get_height())).convert_alpha()
    black.fill((0, 0, 0, shadow))
    newsurf.blit(black, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    newsurf = pg.transform.gaussian_blur(expandSurfaceAlpha(newsurf, 6), 4)
    return newsurf

def generateGradientHoriz(col1, col2, w=1336, h=768, a1=255, a2=255):
    r1, g1, b1 = col1[0], col1[1], col1[2]
    r2, g2, b2 = col2[0], col2[1], col2[2]
    surface = pg.Surface((w, h))
    surface.fill((0, 0, 0, 0))
    for i in range(w):
        tr = i/(w-1)
        pg.draw.line(surface, ((r1*(1-tr) + r2*tr), (g1*(1-tr) + g2*tr), (b1*(1-tr) + b2*tr), (a1*(1-tr) + a2*tr)), (i, 0), (i, h))
    return surface

def fallback(val, fallback):
    return val if val["value"] != None else fallback

def getWeather():
    global weather
    global loadingtext
    global loadingstage
    global wttr
    global redmode
    redmode = False
    wttr = not getattr(vars, "forcecoords", False)
    loadingstage=0
    loadingtext="Loading..."
    if wttr:
        try:
            weather = r.get(weatheraddr, headers=rheaders).json()
            weatherend = r.get(f'https://api.weather.gov/points/{weather["nearest_area"][0]["latitude"]},{weather["nearest_area"][0]["longitude"]}', headers=rheaders).json()
        except:
            wttr = False
            print("Error: Wttr.in is down! Please input your coordinates (lat,long).")
            if getattr(vars, "coords", False):
                coords = getattr(vars, "coords")
            else:
                coords = input("coordinates: ")
            weatherend = r.get(f'https://api.weather.gov/points/{coords}', headers=rheaders).json()
    else:
        if getattr(vars, "coords", False):
            coords = getattr(vars, "coords")
        else:
            coords = input("coordinates: ")
        weatherend = r.get(f'https://api.weather.gov/points/{coords}', headers=rheaders).json()
    loadingstage=1
    loadingtext="Retrieving stations..."
    weatherendpoint1 = weatherend["properties"]["observationStations"]
    weatherendpoint2 = weatherend["properties"]["forecast"]
    weatherendpoint3 = weatherend["properties"]["forecastHourly"]
    weatherendpoint4 = weatherend["properties"]["forecastGridData"]
    stationname = r.get(weatherendpoint1, headers=rheaders).json()["features"][0]["properties"]["stationIdentifier"]
    print(stationname)
    global weather2 # current
    loadingstage=2
    loadingtext="Retrieving current\nconditions..."
    weather2 = r.get(f'https://api.weather.gov/stations/{stationname}/observations', headers=rheaders).json()
    loadingtext="Retrieving station\ninformation..."
    global stationinfo
    stationinfo = r.get(f'https://api.weather.gov/stations/{stationname}/', headers=rheaders).json()
    global weather3 # forecast
    loadingtext="Retrieving forecast..."
    loadingstage=3
    weather3 = r.get(weatherendpoint2, headers=rheaders).json()
    global weather4
    weather4 = r.get(weatherendpoint3, headers=rheaders).json()
    global weatherraw
    weatherraw = r.get(weatherendpoint4, headers=rheaders).json()
    global alerts
    if wttr:
        alerts = r.get(f'https://api.weather.gov/alerts/active?message_type=alert&point={weather["nearest_area"][0]["latitude"]},{weather["nearest_area"][0]["longitude"]}', headers=rheaders).json()["features"]
    else:
        alerts = r.get(f'https://api.weather.gov/alerts/active?message_type=alert&point={coords}', headers=rheaders).json()["features"]
    global weathericons
    global weathericonbig
    loadingtext="Loading icons..."
    weathericons = [None for _ in range(14)]
    loadingstage=4
    for i in range(14):
        weathericons[i] = pg.image.load(BytesIO(r.get(weather3["properties"]["periods"][i]["icon"]+"&size=128", headers=rheaders).content))
    if weather2["features"][0]["properties"]["icon"]:
        weathericonbig = pg.image.load(BytesIO(r.get(weather2["features"][0]["properties"]["icon"]+"&size=192", headers=rheaders).content))
    else:
        weathericonbig = pg.image.load(BytesIO(r.get(weather3["properties"]["periods"][0]["icon"]+"&size=192", headers=rheaders).content))
    loadingtext="Loading images..."
    global bigforecast1
    global bigforecast2
    global trackhurricanes
    trackhurricanes = False
    global radarimage
    radarimage = pg.image.load(BytesIO(r.get(warnsurl, headers=rheaders).content))
    global hurricaneimage
    hurricaneimage = pg.image.load(BytesIO(r.get(f"https://www.nhc.noaa.gov/xgtwo/two_{getattr(vars, 'hurricanesector', 'pac').lower()}_0d0.png", headers=rheaders).content))
    if partnered:
        loadingtext = "Loading your logo..."
        global logosurf
        logosurf = pg.image.load(partnerlogo)
    for alert in alerts:
        print(alert["properties"]["status"])
        print(alert["properties"]["certainty"])
        print(alert["properties"]["urgency"])
        if not alert["properties"]["status"] == "Actual":
            continue
        if not alert["properties"]["certainty"] in ["Observed", "Likely"]:
            continue
        if not alert["properties"]["urgency"] in ["Immediate", "Expected"]:
            continue
        redmode = True
        if "hurricane" in alert["properties"]["description"].lower():
            trackhurricanes = True
    if not redmode:
        bigforecast1 = pg.image.load(BytesIO(r.get(gtempurl, headers=rheaders).content))
    else:
        bigforecast1 = pg.image.load(BytesIO(r.get(warnsurl, headers=rheaders).content))
    bigforecast2 = pg.image.load(BytesIO(r.get(grainurl, headers=rheaders).content))
    
    
    global loading
    loading = False

def refreshWeather():
    global weather
    global weather2
    global weather3
    global weather4
    global weatherraw
    global loadingtext
    global loadingstage
    global wttr
    global redmode
    global alerts
    global weathericons
    global weathericonbig
    global stationinfo
    
    if wttr:
        try:
            weather = r.get(weatheraddr, headers=rheaders).json()
            weatherend = r.get(f'https://api.weather.gov/points/{weather["nearest_area"][0]["latitude"]},{weather["nearest_area"][0]["longitude"]}', headers=rheaders).json()
        except:
            wttr = False
            print("Error: Wttr.in is down! Please input your coordinates (lat,long).")
            if getattr(vars, "coords", False):
                coords = getattr(vars, "coords")
            else:
                coords = input("coordinates: ")
            weatherend = r.get(f'https://api.weather.gov/points/{coords}', headers=rheaders).json()
    else:
        if getattr(vars, "coords", False):
            coords = getattr(vars, "coords")
        else:
            coords = input("coordinates: ")
        weatherend = r.get(f'https://api.weather.gov/points/{coords}', headers=rheaders).json()
    weatherendpoint1 = weatherend["properties"]["observationStations"]
    weatherendpoint2 = weatherend["properties"]["forecast"]
    weatherendpoint3 = weatherend["properties"]["forecastHourly"]
    weatherendpoint4 = weatherend["properties"]["forecastGridData"]
    stationname = r.get(weatherendpoint1, headers=rheaders).json()["features"][0]["properties"]["stationIdentifier"]
    print(stationname)
    weather2 = r.get(f'https://api.weather.gov/stations/{stationname}/observations', headers=rheaders).json()
    stationinfo = r.get(f'https://api.weather.gov/stations/{stationname}/', headers=rheaders).json()
    weather3 = r.get(weatherendpoint2, headers=rheaders).json()
    weather4 = r.get(weatherendpoint3, headers=rheaders).json()
    weatherraw = r.get(weatherendpoint4, headers=rheaders).json()
    if wttr:
        alerts = r.get(f'https://api.weather.gov/alerts/active?message_type=alert&point={weather["nearest_area"][0]["latitude"]},{weather["nearest_area"][0]["longitude"]}', headers=rheaders).json()["features"]
    else:
        alerts = r.get(f'https://api.weather.gov/alerts/active?message_type=alert&point={coords}', headers=rheaders).json()["features"]
    
    for i in range(14):
        weathericons[i] = pg.image.load(BytesIO(r.get(weather3["properties"]["periods"][i]["icon"]+"&size=128", headers=rheaders).content))
    if weather2["features"][0]["properties"]["icon"]:
        weathericonbig = pg.image.load(BytesIO(r.get(weather2["features"][0]["properties"]["icon"]+"&size=192", headers=rheaders).content))
    else:
        weathericonbig = pg.image.load(BytesIO(r.get(weather3["properties"]["periods"][0]["icon"]+"&size=192", headers=rheaders).content))
    global bigforecast1
    global bigforecast2
    bigforecast1 = pg.image.load(BytesIO(r.get(gtempurl, headers=rheaders).content))
    bigforecast2 = pg.image.load(BytesIO(r.get(grainurl, headers=rheaders).content))
    global trackhurricanes
    trackhurricanes = False
    global hurricaneimage
    hurricaneimage = pg.image.load(BytesIO(r.get(f"https://www.nhc.noaa.gov/xgtwo/two_{getattr(vars, 'hurricanesector', 'pac').lower()}_0d0.png", headers=rheaders).content))
    global radarimage
    radarimage = pg.image.load(BytesIO(r.get(warnsurl, headers=rheaders).content))
    for alert in alerts:
        if not alert["properties"]["status"] == "Actual":
            continue
        if not alert["properties"]["certainty"] in ["Observed", "Likely"]:
            continue
        if not alert["properties"]["urgency"] in ["Immediate", "Expected"]:
            continue
        redmode = True
        if "hurricane" in alert["properties"]["description"].lower():
            trackhurricanes = True

class RepeatTimer(th.Timer):
    def run(self):  
        while not self.finished.wait(self.interval):  
            self.function(*self.args,**self.kwargs)

rrt = RepeatTimer(60, refreshWeather)
rrt.daemon = True
rrt.start()

gradient = generateGradient((0, 80, 255), (0, 180,  255))
gradientred = generateGradient((255, 0, 0), (255, 90, 0))
topgradient = generateGradientHoriz((34, 139, 34), (124, 252, 0), h=64)
bottomgradient = generateGradientHoriz((240, 128, 128), (178, 34, 34), h=64)
bottomgradientred = generateGradientHoriz((0, 80, 255), (0, 180,  255), h=64)
topshadow = generateGradient((127, 127, 127), (255, 255, 255), a1=127, a2=0, h=16)
bottomshadow = generateGradient((255, 255, 255), (127, 127, 127), a1=127, a2=0, h=16)

weekbg = generateGradient((0, 140, 255), (0, 40, 255), w=140, h=556)
weekbg.blit(generateGradient((0, 40, 255), (0, 140,  255), w=130, h=546), (5, 5))

weekbgn = generateGradient((140, 140, 140), (40, 40, 40), w=140, h=556)
weekbgn.blit(generateGradient((40, 40, 40), (140, 140,  140), w=130, h=546), (5, 5))

weekbgc = generateGradient((0, 140, 255), (0, 40, 255), w=140, h=276)
weekbgc.blit(generateGradient((0, 40, 255), (0, 140,  255), w=130, h=266), (5, 5))

weekbgnc = generateGradient((140, 140, 140), (40, 40, 40), w=140, h=276)
weekbgnc.blit(generateGradient((40, 40, 40), (140, 140,  140), w=130, h=266), (5, 5))

graphbg = generateGradient((0, 140, 255), (0, 40, 255), w=(994+312), h=556)
graphbg.blit(generateGradient((0, 40, 255), (0, 140, 255), w=(984+312), h=546), (5, 5))

fontname = getattr(vars, "font", "Arial")
bold = True
sizemult = 1
if getattr(vars, "sysfont", True):
    smallfont = pg.font.SysFont(fontname, round(24 * sizemult), bold=bold)
    smallishfont = pg.font.SysFont(fontname, round(33 * sizemult), bold=bold)
    smallmedfont = pg.font.SysFont(fontname, round(42 * sizemult), bold=bold)
    medfont = pg.font.SysFont(fontname, round(60 * sizemult), bold=bold)
    bigfont = pg.font.SysFont(fontname, round(96 * sizemult), bold=bold)
    hugefont = pg.font.SysFont(fontname, round(144 * sizemult), bold=bold)
    giganticfont = pg.font.SysFont(fontname, round(320 * sizemult), bold=bold)
else:
    smallfont = pg.font.Font(fontname, round(24 * sizemult))
    smallishfont = pg.font.Font(fontname, round(33 * sizemult))
    smallmedfont = pg.font.Font(fontname, round(42 * sizemult))
    medfont = pg.font.Font(fontname, round(60 * sizemult))
    bigfont = pg.font.Font(fontname, round(96 * sizemult))
    hugefont = pg.font.Font(fontname, round(144 * sizemult))
    giganticfont = pg.font.Font(fontname, round(320 * sizemult))
weatherth = th.Thread(target=getWeather, daemon=True)
weatherth.start()

def alphablit(surf, alpha, coord):
    transparent = pg.surface.Surface((surf.get_width(), surf.get_height())).convert_alpha()
    transparent.fill((255, 255, 255, alpha))
    transparent.blit(surf, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(transparent, coord)

def expandSurface(surf, expansion):
    newsurf = pg.surface.Surface((surf.get_width() + expansion*2, surf.get_height() + expansion*2))
    newsurf.fill((255, 255, 255, 0))
    newsurf.blit(surf, (expansion, expansion))
    return newsurf

def expandSurfaceAlpha(surf, expansion):
    newsurf = pg.surface.Surface((surf.get_width() + expansion*2, surf.get_height() + expansion*2)).convert_alpha()
    newsurf.fill((255, 255, 255, 0))
    newsurf.blit(surf, (expansion, expansion))
    return newsurf

def drawshadowtext(text, size, x, y, offset, shadow=127):
    text = str(text)
    usecache = True
    if text in textcache:
        if size in textcache[text]:
            textn = textcache[text][size][0]
            textsh = textcache[text][size][1]
            textbland = textcache[text][size][2]
        else:
            usecache = False
    else:
        usecache = False
    debugsleep()
    
    if not usecache:
        textn = size.render(text, 1, (255, 255, 255, 0))
        textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
        textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
        if not text in textcache:
            textcache[text] = {}
        textcache[text][size] = []
        textcache[text][size].append(textn)
        textcache[text][size].append(textsh)
        textbland = size.render(text, 1, (255, 255, 255, 255))
        textcache[text][size].append(textbland)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return textbland

def drawshadowtemp(temp, size: pg.font.Font, x, y, offset, shadow=127):
    temp = str(temp)
    usecache = True
    if temp in tempcache:
        if size in tempcache[temp]:
            textn = tempcache[temp][size][0]
            textsh = tempcache[temp][size][1]
        else:
            usecache = False
    else:
        usecache = False
    
    if not usecache:
        textn = size.render(temp, 1, (255, 255, 255, 255))
        textsh = size.render(temp, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
        if len(temp) == 3:
            textn = pg.transform.smoothscale_by(textn, (2/3, 1))
            textsh = pg.transform.smoothscale_by(textsh, (2/3, 1))
        textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
        if not temp in tempcache:
            tempcache[temp] = {}
        tempcache[temp][size] = []
        tempcache[temp][size].append(textn)
        tempcache[temp][size].append(textsh)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return textn
def drawshadowcrunch(text, size: pg.font.Font, x, y, offset, targetWidth, shadow=127):
    textn = size.render(text, 1, (255, 255, 255, 255))
    textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
    if size.size(text)[0] > targetWidth:
        textn = pg.transform.smoothscale(textn, (targetWidth, size.size(text)[1]))
        textsh = pg.transform.smoothscale(textsh, (targetWidth, size.size(text)[1]))
    textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return textn

def mapnum(minv, maxv, nminv, nmaxv, val):
    firstspan = maxv-minv
    secondspan = nmaxv-nminv
    valsc = val-minv
    return nminv + ((valsc / firstspan) * secondspan)

def drawshadowtextcol(text, col, size, x, y, offset, shadow=127):
    text = str(text)
    usecache = True
    
    if text in textcachecol:
        if size in textcachecol[text]:
            if col in textcachecol[text][size]:
                textn = textcachecol[text][size][col][0]
                textsh = textcachecol[text][size][col][1]
                textbland = textcachecol[text][size][col][2]
            else:
                usecache = False
        else:
            usecache = False
    else:
        usecache = False
    
    usecache = False
    
    if not usecache:
        textn = size.render(text, 1, col)
        textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
        textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
        window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
        window.blit(textn, (x, y))
        if text in textcachecol:
            if not size in textcachecol[text]:
                textcachecol[text][size] = {}
        else:
            textcachecol[text] = {}
            textcachecol[text][size] = {}
        textcachecol[text][size][col] = []
        textbland = size.render(text, 1, (255, 255, 255, 255))
        textcachecol[text][size][col].append(textn)
        textcachecol[text][size][col].append(textsh)
        textcachecol[text][size][col].append(textbland)
    return size.render(text, 1, (255, 255, 255, 255))

def drawshadowcrunchcol(text, col, size, x, y, offset, targetWidth, shadow=127):
    text = str(text)
    textn = size.render(text, 1, col)
    textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
    if size.size(text)[0] > targetWidth:
        textn = pg.transform.smoothscale(textn, (targetWidth, size.size(text)[1]))
        textsh = pg.transform.smoothscale(textsh, (targetWidth, size.size(text)[1]))
    textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return size.render(text, 1, (255, 255, 255, 255))

def getcrunch(text, size, targetWidth, targetHeight):
    text = str(text)
    textn = size.render(text, 1, (255, 255, 255))
    textsh = size.render(text, 1, (0, 0, 0))
    crunchw = 1
    crunchh = 1
    if textn.get_width() > targetWidth:
        crunchw = targetWidth/textn.get_width()
    if textn.get_height() > targetHeight:
        crunchh = targetHeight/textsh.get_height()
    return crunchw, crunchh, textn.get_width(), textsh.get_height()

def drawshadowbigcrunch(text, col, size, x, y, offset, targetWidth, targetHeight, shadow=127):
    text = str(text)
    usecache = True
    
    if text in bigcrunchcache:
        if size in bigcrunchcache[text]:
            if col in bigcrunchcache[text][size]:
                textn = bigcrunchcache[text][size][col][0]
                textsh = bigcrunchcache[text][size][col][1]
                textbland = bigcrunchcache[text][size][col][2]
            else:
                usecache = False
        else:
            usecache = False
    else:
        usecache = False
    
    if not usecache:
        textn = size.render(text, 1, col)
        textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
        if textn.get_width() > targetWidth:
            textn = pg.transform.smoothscale_by(textn, (targetWidth/textn.get_width(), 1))
            textsh = pg.transform.smoothscale_by(textsh, (targetWidth/textsh.get_width(), 1))
        if textn.get_height() > targetHeight:
            textn = pg.transform.smoothscale_by(textn, (1, targetHeight/textn.get_height()))
            textsh = pg.transform.smoothscale_by(textsh, (1, targetHeight/textsh.get_height()))
        textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
        if text in bigcrunchcache:
            if size in bigcrunchcache[text]:
                if not col in bigcrunchcache[text][size]:
                    bigcrunchcache[text][size][col] = []
            else:
                bigcrunchcache[text][size] = {}
                bigcrunchcache[text][size][col] = []
        else:
            bigcrunchcache[text] = {}
            bigcrunchcache[text][size] = {}
            bigcrunchcache[text][size][col] = []
        textbland = size.render(text, 1, (255, 255, 255, 255))
        bigcrunchcache[text][size][col].append(textn)
        bigcrunchcache[text][size][col].append(textsh)
        bigcrunchcache[text][size][col].append(textbland)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return textbland

def drawshadowtempcol(temp, col, size: pg.font.Font, x, y, offset, shadow=127):
    temp = str(temp)
    usecache = True
    if temp in tempcachecol:
        if size in tempcachecol[temp]:
            if col in tempcachecol[temp][size]:
                textn = tempcachecol[temp][size][col][0]
                textsh = tempcachecol[temp][size][col][1]
            else:
                usecache = False
        else:
            usecache = False
    else:
        usecache = False
    
    if not usecache:
        textn = size.render(temp, 1, col)
        textsh = size.render(temp, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
        if len(temp) == 3:
            textn = pg.transform.smoothscale_by(textn, (2/3, 1))
            textsh = pg.transform.smoothscale_by(textsh, (2/3, 1))
        textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
        if temp in tempcachecol:
            if size in tempcachecol[temp]:
                if not col in tempcachecol[temp][size]:
                    tempcachecol[temp][size][col] = []
            else:
                tempcachecol[temp][size] = {}
                tempcachecol[temp][size][col] = []
        else:
            tempcachecol[temp] = {}
            tempcachecol[temp][size] = {}
            tempcachecol[temp][size][col] = []
        tempcachecol[temp][size][col].append(textn)
        tempcachecol[temp][size][col].append(textsh)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return textn

def parsetimelength(timestamp):
    time = timestamp.split("/")[1]
    #2DT6H for example
    finalhours = 0
    delt = it.parse_duration(time)
    days = delt.days
    secs = delt.seconds
    secs /= 3600
    secs = int(secs)
    finalhours += days*24
    finalhours += secs
    return finalhours
def parseRawTimeStamp(timestamp):
    time = dt.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S+00:00/"+timestamp.split("/")[1])
    time = time - dt.timedelta(hours=4)
    periodtime = parsetimelength(timestamp)
    return (time, time + dt.timedelta(hours=periodtime), periodtime)

def nonezero(val):
    return 0 if val == None else val

def getValuesHourly(values):
    #we need to get 24 hours of values
    
    #find offset
    now = dt.datetime.now()
    offset = 0
    alltimes = []
    for value in range(len(values)):
        ti = values[value]["validTime"].split("/")[0]
        length = it.parse_duration(values[value]["validTime"].split("/")[1])
        time = it.parse_datetime(ti).astimezone(tz.timezone(getattr(vars, "timezone", "EST")))
        tim = length.seconds / 3600
        tim += length.days * 24
        for i in range(int(tim)):
            alltimes.append((time + dt.timedelta(hours=i)).astimezone(tz.timezone(getattr(vars, "timezone", "EST"))))
    now.replace(tzinfo=tz.timezone(getattr(vars, "timezone", "EST")))
    for time in range(len(alltimes)):
        if now.astimezone(tz.timezone(getattr(vars, "timezone", "EST"))) > alltimes[time].astimezone(tz.timezone(getattr(vars, "timezone", "EST"))):
            offset = time
    vals = []
    for value in values:
        val = value["value"]
        tstart, tend, t = parseRawTimeStamp(value["validTime"])
        for i in range(t):
            vals.append(int(val))
        if len(vals) >= 25+offset:
            break
    if len(vals) < 25+offset:
        while len(vals) < 25+offset:
            vals.append(vals[-1])
    return vals[offset:(25+offset)]

def makehourlygraph():
    w = 984+312
    h = 546
    surf = pg.Surface((w, h)).convert_alpha()
    surf2 = pg.Surface((w, h)).convert_alpha()
    
    temps = []
    cloud = getValuesHourly(weatherraw["properties"]["relativeHumidity"]["values"])
    precip = getValuesHourly(weatherraw["properties"]["probabilityOfPrecipitation"]["values"])
    #for val in getValuesHourly(weatherraw["properties"]["temperature"]["values"]):
    #    temps.append(round(float(val)*1.8+32))
    offset = 0
    for pd in weather4["properties"]["periods"][(0+offset):(25+offset)]:
        temps.append(round(float(pd["temperature"])))
    mintemp = min(temps)
    maxtemp = max(temps)
    medtemp = round((mintemp+maxtemp)/2)
    #time = dt.now(tz.utc)
    #order: cloud, precip, temp
    surf.fill((255, 255, 255, 0))
    surf2.fill((255, 255, 255))
    
    for i in range(24):
        pg.draw.line(surf2, (0, 0, 0), (mapnum(0, 24, 0, w, i), mapnum(100, 0, 0, h-6, cloud[i])+2), (mapnum(0, 24, 0, w, i+1), mapnum(100, 0, 0, h-6, cloud[i+1])+2), 6)
    for i in range(24):
        pg.draw.line(surf, (255, 127, 0), (mapnum(0, 24, 0, w, i), mapnum(100, 0, 0, h-6, cloud[i])), (mapnum(0, 24, 0, w, i+1), mapnum(100, 0, 0, h-6, cloud[i+1])), 3)
    for i in range(24):
        pg.draw.line(surf2, (0, 0, 0), (mapnum(0, 24, 0, w, i), mapnum(100, 0, 0, h-6, precip[i])+2), (mapnum(0, 24, 0, w, i+1), mapnum(100, 0, 0, h-6, precip[i+1])+2), 6)
    for i in range(24):
        pg.draw.line(surf, (0, 255, 255), (mapnum(0, 24, 0, w, i), mapnum(100, 0, 0, h-6, precip[i])), (mapnum(0, 24, 0, w, i+1), mapnum(100, 0, 0, h-6, precip[i+1])), 3)
    for i in range(24):
        pg.draw.line(surf2, (0, 0, 0), (mapnum(0, 24, 0, w, i), mapnum(maxtemp, mintemp, 0, h-6, temps[i])+2), (mapnum(0, 24, 0, w, i+1), mapnum(maxtemp, mintemp, 0, h-6, temps[i+1])+2), 6)
    for i in range(24):
        pg.draw.line(surf, (255, 0, 0), (mapnum(0, 24, 0, w, i), mapnum(maxtemp, mintemp, 0, h-6, temps[i])), (mapnum(0, 24, 0, w, i+1), mapnum(maxtemp, mintemp, 0, h-6, temps[i+1])), 3)
    
    surf2 = pg.transform.gaussian_blur(expandSurface(surf2, 6), 4)
    
    return surf, surf2, {"mintemp": mintemp, "maxtemp": maxtemp, "medtemp": medtemp}

def formatMetric(metric):
    if metric["value"] == None:
        return 404
    if metric["unitCode"] == "wmoUnit:degC":
        return metric["value"]*1.8+32
    elif metric["unitCode"] == "wmoUnit:km_h-1":
        return metric["value"]/1.609
    elif metric["unitCode"] == "wmoUnit:Pa":
        return metric["value"]/3386
    else:
        return metric["value"]

def handleNone(val):
    return val if val != None else 0

def roundd(val, precision):
    if val in [None, "Error"]:
        return "Error"
    else:
        return round(val, precision)

def stripdss(array: list):
    newar = array
    newar.remove(".DS_Store")
    return newar

pg.event.pump()
def main():
    bottomtomorrow = False
    working = True
    playingmusic = 0
    view = 0
    alertscroll = 0
    alertscrollbig = 0
    alertshow = 0
    showingalert = 0
    alertdir = 1
    alerttimer = 300
    clock = pg.time.Clock()
    night = False
    nightv= False
    music = None
    shuffle = 0
    redded = False
    changetime = 60 * 15
    justswitched = True
    
    ticker = 0
    tickertimer = 60 * 4
    
    alerttimeout = 60 * 10
    adindex = -1
    scrollalert = False
    alerttarget = 0
    
    #cache
    
    #currently:
    #hourlygraph
    
    
    sections = 9
    
    try:
        global loading
        loading = True
    except:
        pass
    while working:
        delta = clock.tick(60) / 1000
        for event in pg.event.get():
            if event.type == pg.QUIT:
                working = False
            if not loading:
                if event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == pg.BUTTON_LEFT:
                        bottomtomorrow += 1
                        if bottomtomorrow > 13:
                            bottomtomorrow = 0
                        nightv += 1
                        if nightv > 4:
                            nightv = 0
                        alertshow += 1
                        if alertshow > len(alerts)-1:
                            alertshow = 0
                    elif event.button == pg.BUTTON_RIGHT:
                        bottomtomorrow = 0
                        alertshow = 0
                        nightv = False
                        view += 1
                        if view > sections:
                            view = 0
                        if view == sections and len(alerts) > 0:
                            changetime = 60 * 45
                        else:
                            changetime = 60 * 15
                        justswitched = True
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_EQUALS:
                        pg.display.toggle_fullscreen()
                    if event.key == pg.K_MINUS:
                        shuffle = 1
                    if event.key == pg.K_9:
                        pg.display.iconify()
        if not working:
            break
        window.blit(gradient if not redmode else gradientred, (0, 0))
        if loading:
            loadtext = bigfont.render(loadingtext, 1, (255, 255, 255, 255))
            loadshadow = bigfont.render(loadingtext, 1, (0, 0, 0, 100))
            alphablit(loadshadow, 127, (668-loadtext.get_width()/2+10, 384-loadtext.get_height()/2+10))
            window.blit(loadtext, (668-loadtext.get_width()/2, 384-loadtext.get_height()/2))
        else:
            if not redded:
                if redmode:
                    view = sections
                    changetime = 60 * 30
                redded = True
            if True:
                now = dt.datetime.now()
                obstime = dt.datetime.strptime(weather2["features"][0]["properties"]["timestamp"] + "UTC", "%Y-%m-%dT%H:%M:%S+00:00%Z")
                obstimeshort = obstime.strftime("%I:%M %p")
                if sound:
                    if wttr:
                        sunset = dt.datetime.strptime(weather["weather"][0]["astronomy"][0]["sunset"], timeformat)
                        sunrise = dt.datetime.strptime(weather["weather"][0]["astronomy"][0]["sunrise"], timeformat)
                    night = False
                    if musicmode == "playlist":
                        if not manualmusic:
                            if music == None:
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play()
                            elif not music.get_busy():
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play()
                        else:
                            if music == None:
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play(-1)
                            if shuffle:
                                shuffle = 0
                                music.fadeout(1000)
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play(-1)
                    else:
                        if wttr:
                            if now.hour > sunset.hour:
                                night = True
                            if now.hour < sunrise.hour:
                                night = True
                            if now.hour == sunrise.hour:
                                if now.minute < sunrise.minute:
                                    night = True
                            if now.hour == sunset.hour:
                                if now.minute > sunset.minute:
                                    night = True
                            if not playingmusic:
                                daytheme.play(-1)
                                playingmusic = True
                        else:
                            if (1 + night) != playingmusic:
                                playingmusic = 1 + night
                                if playingmusic == 1:
                                    nighttheme.fadeout(1000)
                                    daytheme.play(-1)
                                elif playingmusic == 2:
                                    daytheme.fadeout(1000)
                                    nighttheme.play(-1)
            periods = weather3["properties"]["periods"]
            currenttemp = giganticfont.render(f'{round(formatMetric(weather2["features"][0]["properties"]["temperature"]))}', 1, (255, 255, 255, 255))
            currentcondition = smallmedfont.render(weather2["features"][0]["properties"]["textDescription"], 1, (255, 255, 255, 255))
            #top bar
            
            # window.blit(topshadow, (0, 64), special_flags=pg.BLEND_RGBA_MULT)
            # window.blit(topgradient, (0, 0))
            
            # if view == 0:
            #     window.blit(topshadow, (0, 524), special_flags=pg.BLEND_RGBA_MULT)
            #     window.blit(topgradient, (0, 460))
            #     drawshadowtext(periods[bottomtomorrow]["name"].upper(), smallmedfont, 5, 465, 5, 127)
            
            # viewnames = ["Split View", "Overview", "7-Day Forecast", "Hourly Graph", f"Weather Report ({periods[0]['name']})", f"Weather Report ({periods[1]['name']})", f"Weather Report ({periods[2]['name']})", "Alerts"]
            # viewName = viewnames[view]
            # if view == 2:
            #     nightv = 4
            #     #force view 2
            #     viewName = ["7-Day Forecast (Day)", "7-Day Forecast (Night)", "7-Day Forecast (Page 1)", "7-Day Forecast (Page 2)", "7-Day Forecast"][nightv]
            # if wttr:
            #     location = smallmedfont.render(weather["nearest_area"][0]["areaName"][0]["value"], 1, (255, 255, 255, 255))
            # drawshadowtext(viewName, smallmedfont, 824-312/2-smallmedfont.size(viewName)[0]/2, 5, 5, 127)
            # drawshadowtext(dt.datetime.now().strftime(timeformattop), smallmedfont, 5, 5, 5, 127)
            # #drawshadowtext(clock.get_fps(), smallmedfont, 5, 5, 5, 127)
            # if wttr:
            #     drawshadowtext(weather["nearest_area"][0]["areaName"][0]["value"], smallmedfont, 1336-10-location.get_width(), 5, 5, 127)
            
            #today
            # today's forecast (min, axg, max) (deprecated)
            #drawshadowtemp("Previous 24h extremes:", smallmedfont, 5, 80, 5, 127)
            #drawshadowtempcol(round(formatMetric(weather2["features"][0]["properties"]["minTemperatureLast24Hours"])), (135, 206, 250, 255), smallmedfont,405, 80, 5, 127)
            #drawshadowtempcol(round(formatMetric(weather2["features"][0]["properties"]["maxTemperatureLast24Hours"])), (255, 140, 0, 255), smallmedfont, 480, 80, 5, 127)
            # alerts
            if view != sections:
                if len(alerts) > 0:
                    if len(alerts) > 1:
                        if alerttimer > 0:
                            alerttimer -= 1 * delta * 60
                        else:
                            alertscroll += 5 * delta * 60
                    if alertscroll > 1336:
                        showingalert += 1
                        alertscroll = 0
                        alerttimer = 300
                        if showingalert > len(alerts)-1:
                            showingalert = 0
                    if not redmode:
                        drawshadowcrunchcol(alerts[showingalert]["properties"]["headline"], (255, 0, 0), smallmedfont, 5 + alertscroll, 80, 5, 1336-15, 127)
                    else:
                        drawshadowcrunchcol(alerts[showingalert]["properties"]["headline"], (0, 127, 255), smallmedfont, 5 + alertscroll, 80, 5, 1336-15, 127)
                    if len(alerts) > 1:
                        drawshadowcrunchcol(alerts[(showingalert+1) if showingalert != len(alerts)-1 else 0]["properties"]["headline"], (255, 0, 0), smallmedfont, -1019 + alertscroll, 80, 5, 1024-15, 127)
                else:
                    drawshadowtext("No active alerts in your area.", smallmedfont, 5, 80, 5, 127)
            # current
            if view in [0, 1]:
                precip = weather2["features"][0]["properties"]["precipitationLastHour"]["value"]
                if precip == None:
                    precip = "0"
                else:
                    precip = str(round(precip/25.4, 1))
                currenttemp = drawshadowtemp(round(formatMetric(weather2["features"][0]["properties"]["temperature"])), giganticfont, 60, 80, 20, 180)
                drawshadowtext("°F", bigfont, currenttemp.get_width()+60, 125, 10, 160)
                if weather2["features"][0]["properties"]["windSpeed"]["value"] != None:
                    #print(weather2["features"][0]["properties"]["windSpeed"])
                    drawshadowtext(f'Wind: {degrees_to_compass(weather2["features"][0]["properties"]["windDirection"]["value"])} @ {round((formatMetric(weather2["features"][0]["properties"]["windSpeed"])))} MPH', smallmedfont, 540, 125, 5, 127)
                else:
                    drawshadowtext('Wind: Calm', smallmedfont, 540, 125, 5, 127)
                drawshadowtext(f'Relative Humidity: {roundd(weather2["features"][0]["properties"]["relativeHumidity"]["value"], 1)}%', smallmedfont, 540, 175, 5, 127)
                drawshadowtext(f'Precipitation: {precip} inches', smallmedfont, 540, 225, 5, 127)
                drawshadowtext(f'Visibility: {round(weather2["features"][0]["properties"]["visibility"]["value"]/1609, 1)} miles', smallmedfont, 540, 275, 5, 127)
                if weather2["features"][0]["properties"]["heatIndex"]['value']:
                    drawshadowtext(f'Heat Index: {round(formatMetric(weather2["features"][0]["properties"]["heatIndex"]))}°F', smallmedfont, 540, 325, 5, 127)
                    drawshadowtext(f'Air pressure: {roundd(formatMetric(weather2["features"][0]["properties"]["barometricPressure"]), 2)} inHg', smallmedfont, 540, 375, 5, 127)
                elif weather2["features"][0]["properties"]["windChill"]['value']:
                    drawshadowtext(f'Wind Chill: {round(formatMetric(weather2["features"][0]["properties"]["windChill"]))}°F', smallmedfont, 540, 325, 5, 127)
                    drawshadowtext(f'Air pressure: {roundd(formatMetric(weather2["features"][0]["properties"]["barometricPressure"]), 2)} inHg', smallmedfont, 540, 375, 5, 127)
                else:
                    drawshadowtext(f'Air pressure: {roundd(formatMetric(weather2["features"][0]["properties"]["barometricPressure"]), 2)} inHg', smallmedfont, 540, 325, 5, 127)
                #window.blit(currenttemp, (60, 80))
                offsetw = -currentcondition.get_width()/2
                if offsetw < -220:
                    offsetw = -220
                
                drawshadowcrunch(weather2["features"][0]["properties"]["textDescription"], smallmedfont, 60+currenttemp.get_width()/2+offsetw, 400, 5, 440, 127)
                
                periods = weather3["properties"]["periods"]
                if view == 0:
                    #tomorrow
                    # forecasted temps
                    tm1 = drawshadowtemp(periods[bottomtomorrow]["temperature"], bigfont, 60, 560, 10, 140)
                    #tm2 = drawshadowtempcol(periods[bottomtomorrow]["temperature"], (135, 206, 250, 255), medfont, 280, 540, 7, 127)
                    #tm3 = drawshadowtempcol(periods[bottomtomorrow]["temperature"], (255, 140, 0, 255), medfont, 280, 610, 7, 127)
                    drawshadowtext("°F", bigfont, tm1.get_width()+60, 560, 10, 140)
                    #drawshadowtextcol("°F", (135, 206, 250, 255), medfont, tm2.get_width()+280, 540, 10, 140)
                    #drawshadowtextcol("°F", (255, 140, 0, 255), medfont, tm3.get_width()+280, 610, 10, 140)
                    buffer = pg.Surface((128, 128))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 128, 128))
                    buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (tm1.get_width() + 190, 560), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(weathericons[bottomtomorrow], (tm1.get_width() + 180, 550))
                    # other metrics
                    prval = periods[bottomtomorrow]["probabilityOfPrecipitation"]["value"]
                    if prval == None:
                        prval = "0"
                    drawshadowtext(f'Precipitation Chance: {prval}%', smallmedfont, 440, 540, 5, 127)
                    drawshadowtext(f'Wind: {periods[bottomtomorrow]["windDirection"]} @ {periods[bottomtomorrow]["windSpeed"]}', smallmedfont, 440, 590, 5, 127)
                    drawshadowcrunch(periods[bottomtomorrow]["shortForecast"], smallmedfont, 440, 640, 5, 1336-440-10, 127)
                else:
                    drawshadowtext("\n".join(wraptext(periods[0]["detailedForecast"], pg.Rect(350, 480, 1336-350-15, 768-64-15), smallishfont)), smallishfont, 350, 480, 5, 127)
                    buffer = pg.Surface((192, 192))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 192, 192))
                    buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (110, 490), special_flags=pg.BLEND_RGBA_MULT)
                    if weathericonbig != None:
                        window.blit(weathericonbig, (100, 480))
            elif view == 2:
                nightv = 4
                nowisday = periods[0]["isDaytime"]
                if nightv <= 1:
                    for i in range(7):
                        buffer = pg.Surface((140, 556))
                        pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 140, 556))
                        buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                        window.blit(buffer, (20 + i*142, 133), special_flags=pg.BLEND_RGBA_MULT)
                        window.blit(weekbg if not nightv else weekbgn, (15 + i*142, 128))
                        if nowisday and i == 0:
                            continue
                        if not nowisday and i == 6 and nightv:
                            continue
                        drawshadowtext(periods[i*2+(not nowisday)+nightv]["name"][0:3].upper(), smallmedfont, 15+i*142+70-smallmedfont.size(periods[i*2+(not nowisday)+nightv]["name"][0:3].upper())[0]/2, 138, 5, 127)
                        drawshadowtemp(periods[i*2+(not nowisday)+nightv]["temperature"], bigfont, 30 + i*142, 168, 5, 127)
                        drawshadowtext("Wind:", smallishfont, 40 + i*142, 300, 5, 127)
                        drawshadowtext(periods[i*2+(not nowisday)+nightv]["windDirection"], medfont, 85+i*142-medfont.size(periods[i*2+(not nowisday)+nightv]["windDirection"])[0]/2, 330, 5, 127)
                        window.blit(weathericons[i*2+(not nowisday)+nightv], (21+142*i, 417+128+5))
                elif nightv <= 3:
                    for i in range(7):
                        buffer = pg.Surface((140, 556))
                        pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 140, 556))
                        buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                        window.blit(buffer, (20 + i*142, 133), special_flags=pg.BLEND_RGBA_MULT)
                        drawnight = (i % 2 == 0)
                        offset = not nowisday
                        if not nowisday:
                            drawnight = not drawnight
                        if nightv in [2, 3]:
                            drawnight = not drawnight
                        if nightv == 3:
                            drawnight = not drawnight
                        window.blit(weekbg if not drawnight else weekbgn, (15 + i*142, 128))
                        if nowisday and i in [0, 1] and nightv == 2:
                            continue
                        if not nowisday and i >= 5 and nightv == 3:
                            continue
                        drawshadowtext(periods[i+offset+(nightv-2)*7]["name"][0:3].upper(), smallmedfont, 15+i*142+70-smallmedfont.size(periods[i+offset+(nightv-2)*7]["name"][0:3].upper())[0]/2, 138, 5, 127)
                        drawshadowtemp(periods[i+offset+(nightv-2)*7]["temperature"], bigfont, 30 + i*142, 168, 5, 127)
                        drawshadowtext("Wind:", smallishfont, 40 + i*142, 300, 5, 127)
                        drawshadowtext(periods[i+offset+(nightv-2)*7]["windDirection"], medfont, 85+i*142-medfont.size(periods[i+offset+(nightv-2)*7]["windDirection"])[0]/2, 330, 5, 127)
                        window.blit(weathericons[i+offset+(nightv-2)*7], (21+142*i, 417+128+5))
                else:
                    if justswitched and "7daybuffer" not in cache:
                        buffer = pg.Surface((140, 276))
                        pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 140, 276))
                        buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                        cache["7daybuffer"] = buffer
                    else:
                        buffer = cache["7daybuffer"]
                    for j in range(14):
                        i = j%7
                        drawingn = (j > 6)
                        window.blit(buffer, (20 + 156 + i*142 - 156*partnered, 133+280*drawingn), special_flags=pg.BLEND_RGBA_MULT)
                        window.blit(weekbgc if not drawingn else weekbgnc, (15 + 156 + i*142 - 156*partnered, 128+280*drawingn))
                        if nowisday and i == 0:
                            continue
                        if not nowisday and i == 6 and drawingn:
                            continue
                        drawshadowtext(periods[i*2+(not nowisday)+drawingn]["name"][0:3].upper(), smallmedfont, 15+ 156 +i*142 - 156*partnered+70-smallmedfont.size(periods[i*2+(not nowisday)+drawingn]["name"][0:3].upper())[0]/2, 138+280*drawingn, 5, 127)
                        drawshadowtemp(periods[i*2+(not nowisday)+drawingn]["temperature"], medfont, 52 + 156 - 156*partnered + i*142, 172+280*drawingn, 5, 127)
                        if weathericons[i*2+(not nowisday)+drawingn] != None:
                            window.blit(weathericons[i*2+(not nowisday)+drawingn], (21+ 156 +142*i - 156*partnered, 417+128+5-280*(not drawingn)))
                        drawshadowtext(f'Wind: {periods[i+(drawingn-2)*7]["windDirection"]}', smallfont, 84+ 156 - 156*partnered +i*142-smallfont.size(f'Wind: {periods[i+(drawingn-2)*7]["windDirection"]}')[0]/2, 234+280*drawingn, 5, 127)
                    if partnered:
                        window.blit(turnintoashadow(logosurf), (20 + 142 * 7, 138))
                        window.blit(logosurf, (15 + 142 * 7, 133))
            elif view == 3:
                if justswitched:
                    g, gs, vs = makehourlygraph()
                    cache["hourlygraph"] = [g, gs, vs]
                else:
                    g, gs, vs = cache["hourlygraph"]
                buffer = pg.Surface((994+312, 556))
                pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 994+312, 556))
                buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                window.blit(buffer, (20, 133), special_flags=pg.BLEND_RGBA_MULT)
                window.blit(graphbg, (15, 128))
                window.blit(gs, (20, 133), special_flags=pg.BLEND_RGBA_MULT)
                window.blit(g, (20, 133))
                now = dt.datetime.now()
                now6 = dt.datetime.now() + dt.timedelta(hours=6)
                now12 = dt.datetime.now() + dt.timedelta(hours=12)
                now18= dt.datetime.now() + dt.timedelta(hours=18)
                now24 = dt.datetime.now() + dt.timedelta(hours=24)
                time1 = now.strftime("%I") + ("AM" if (now.strftime("%p") == "AM") else "PM")
                time2 = now6.strftime("%I") + ("AM" if (now6.strftime("%p") == "AM") else "PM")
                time3 = now12.strftime("%I") + ("AM" if (now12.strftime("%p") == "AM") else "PM")
                time4 = now18.strftime("%I") + ("AM" if (now18.strftime("%p") == "AM") else "PM")
                time5 = now24.strftime("%I") + ("AM" if (now24.strftime("%p") == "AM") else "PM")
                drawshadowtext(f'{round(vs["maxtemp"])}°', smallmedfont, 20, 128, 5)
                drawshadowtext(f'{round(vs["medtemp"])}°', smallmedfont, 20, 128+440/2, 5)
                drawshadowtext(f'{round(vs["mintemp"])}°', smallmedfont, 20, 128+440, 5)
                drawshadowtext(time1, smallmedfont, 20, 128+500, 5)
                drawshadowtext(time2, smallmedfont, (1336-640+530)/4 + 15, 128+500, 5)
                drawshadowtext(time3, smallmedfont, (1336-640+530)/2 + 10, 128+500, 5)
                drawshadowtext(time4, smallmedfont, (1336-640+530)*3/4 + 5, 128+500, 5)
                drawshadowtext(time5, smallmedfont, 1336-640+530, 128+500, 5)
                drawshadowtextcol("Temperature", (255, 0, 0), smallmedfont, 1336-16-smallmedfont.size("Temperature")[0], 128, 5, 127)
                drawshadowtextcol("Precipitation %", (0, 255, 255), smallmedfont, 1336-16-smallmedfont.size("Precipitation %")[0], 168, 5, 127)
                drawshadowtextcol("Rel. Humidity %", (255, 127, 0), smallmedfont, 1336-16-smallmedfont.size("Rel. Humidity %")[0], 208, 5, 127)
            elif view == 4:
                drawshadowbigcrunch("\n".join(wraptext(f'{periods[0]["name"]}...{periods[0]["detailedForecast"]}', pg.Rect(15, 128, 994+312, 588+32), smallmedfont)), (255, 255, 255), smallmedfont, 15, 128, 5, 994+312, 588+32, 127)
            elif view == 5:
                drawshadowbigcrunch("\n".join(wraptext(f'{periods[1]["name"]}...{periods[1]["detailedForecast"]}', pg.Rect(15, 128, 994+312, 588+32), smallmedfont)), (255, 255, 255), smallmedfont, 15, 128, 5, 994+312, 588+32, 127)
            elif view == 6:
                drawshadowbigcrunch("\n".join(wraptext(f'{periods[2]["name"]}...{periods[2]["detailedForecast"]}', pg.Rect(15, 128, 994+312, 588+32), smallmedfont)), (255, 255, 255), smallmedfont, 15, 128, 5, 994+312, 588+32, 127)
            elif view == 7:
                if not redmode:
                    buffer = pg.Surface((bigforecast1.get_width(), bigforecast1.get_height()))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, bigforecast1.get_width(), bigforecast1.get_height()))
                    buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (1336/2-bigforecast1.get_width()/2+5, 800/2-bigforecast1.get_height()/2+5), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(bigforecast1, (1336/2-bigforecast1.get_width()/2, 800/2-bigforecast1.get_height()/2))
                else:
                    buffer = pg.Surface((radarimage.get_width(), radarimage.get_height()))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, radarimage.get_width(), radarimage.get_height()))
                    buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (1336/2-radarimage.get_width()/2+5, 800/2-radarimage.get_height()/2+5), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(radarimage, (1336/2-radarimage.get_width()/2, 800/2-radarimage.get_height()/2))
            elif view == 8:
                if not trackhurricanes:
                    buffer = pg.Surface((bigforecast2.get_width(), bigforecast2.get_height()))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, bigforecast2.get_width(), bigforecast2.get_height()))
                    buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (1336/2-bigforecast2.get_width()/2+5, 800/2-bigforecast2.get_height()/2+5), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(bigforecast2, (1336/2-bigforecast2.get_width()/2, 800/2-bigforecast2.get_height()/2))
                else:
                    buffer = pg.Surface((hurricaneimage.get_width(), hurricaneimage.get_height()))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, hurricaneimage.get_width(), hurricaneimage.get_height()))
                    buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (1336/2-hurricaneimage.get_width()/2+5, 800/2-hurricaneimage.get_height()/2+5), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(hurricaneimage, (1336/2-hurricaneimage.get_width()/2, 800/2-hurricaneimage.get_height()/2))
            elif view == 9:
                if justswitched:
                    alertscrollbig = 0
                    alerttimeout = 60 * 10
                scrollalert = False
                if len(alerts) > 0:
                    fnt = smallmedfont
                    if getcrunch(alerts[alertshow]["properties"]["description"], smallmedfont, 994+312, 588)[0] < 1:
                        fnt = smallishfont
                        if getcrunch(alerts[alertshow]["properties"]["description"], smallishfont, 994+312, 588)[1] < 0.75:
                            scrollalert = True
                            alerttarget = getcrunch(alerts[alertshow]["properties"]["description"], smallishfont, 994+312, 588)[3] + 5 - 588
                    elif getcrunch(alerts[alertshow]["properties"]["description"], smallmedfont, 994+312, 588)[1] < 0.75:
                        fnt = smallishfont
                        if getcrunch(alerts[alertshow]["properties"]["description"], smallishfont, 994+312, 588)[1] < 0.75:
                            scrollalert = True
                            alerttarget = getcrunch(alerts[alertshow]["properties"]["description"], smallfont, 994+312, 588)[3] + 5 - 588
                    
                    if alerttimeout <= 0:
                        if scrollalert:
                            if alertdir == 1:
                                if alertscrollbig < alerttarget:
                                    alertscrollbig += 60 * delta
                                else:
                                    alertscrollbig = alerttarget
                                    alertdir = -1
                                    alerttimeout = 60 * 10
                            else:
                                if alertscrollbig > 0:
                                    alertscrollbig -= 60 * delta
                                else:
                                    alertscrollbig = 0
                                    alertdir = 1
                                    alerttimeout = 60 * 10
                    else:
                        alerttimeout -= 60 * delta
                    
                    if scrollalert:
                        drawshadowbigcrunch(alerts[alertshow]["properties"]["description"], (255, 224, 224), fnt, 15, 96-alertscrollbig, 5, 994+312, 9999, 127)
                    else:
                        alertscroll = 0
                        drawshadowbigcrunch(alerts[alertshow]["properties"]["description"], (255, 224, 224), fnt, 15, 96, 5, 994+312, 588, 127)
                else:
                    drawshadowtext("No active alerts.", smallmedfont, 15, 96, 5, 127)
            #housekeeping
            window.blit(bottomgradient if not redmode else bottomgradientred, (0, 704))
            
            if tickertimer <= 0:
                ticker += 1
                if ticker > 6:
                    ticker = 0
                if ticker == 6:
                    tickertimer = 60 * actime
                else:
                    tickertimer = 60 * 4
                    adindex += 1
                    if adindex > len(ads)-1:
                        adindex = 0
            else:
                tickertimer -= 60 * delta
            
            tickerright = ""
            if ticker == 0:
                tickername = f'Last updated at {obstimeshort} UTC'
            elif ticker == 1:
                tickername = f'Temperature: {round(weather2["features"][0]["properties"]["temperature"]["value"]*1.8+32)}°F'
                if weather2["features"][0]["properties"]["heatIndex"]["value"]:
                    tickerright = f'Heat Index: {round(weather2["features"][0]["properties"]["heatIndex"]["value"]*1.8+32)}°F'
                elif weather2["features"][0]["properties"]["windChill"]["value"]:
                    tickerright = f'Wind Chill: {round(weather2["features"][0]["properties"]["windChill"]["value"]*1.8+32)}°F'
            elif ticker == 2:
                tickername = f'Humidity: {round(weather2["features"][0]["properties"]["relativeHumidity"]["value"])}%'
                tickerright = f'Dewpoint: {round(weather2["features"][0]["properties"]["dewpoint"]["value"]*1.8+32)}°F'
            elif ticker == 3:
                tickername = f'Barometric Pressure: {round(weather2["features"][0]["properties"]["barometricPressure"]["value"]/3386, 2)}'
            elif ticker == 4:
                if weather2["features"][0]["properties"]["windDirection"]["value"]:
                    tickername = f'Wind: {degrees_to_compass(weather2["features"][0]["properties"]["windDirection"]["value"])} @ {round(weather2["features"][0]["properties"]["windSpeed"]["value"])} mph'
                else:
                    if weather2["features"][0]["properties"]["windSpeed"]["value"] != None:
                        if weather2["features"][0]["properties"]["windSpeed"]["value"] > 0:
                            tickername = f'Wind: {round(weather2["features"][0]["properties"]["windSpeed"]["value"]/1.609)} mph'
                        else:
                            tickername = "Wind: Calm"
                    else:
                        tickername = "Wind: Calm"
            elif ticker == 5:
                ceiling = nonezero(weather2["features"][0]["properties"]["cloudLayers"][0]["base"]["value"])*3.281
                tickername = f'Visibility: {round(weather2["features"][0]["properties"]["visibility"]["value"]/1609)} miles'
                tickerright = f'Ceiling: {"Unlimited" if ceiling == 0 else f"{round(ceiling/100)*100} feet"}'
            elif ticker == 6:
                tickername = ads[adindex]
            drawshadowtext(tickername, smallmedfont, 5, 768-64+5, 5, 127)
            drawshadowtext(tickerright, smallmedfont, 1336-5-smallmedfont.size(tickerright)[0], 768-64+5, 5, 127)
            window.blit(bottomshadow, (0, 768-64-16), special_flags=pg.BLEND_RGBA_MULT)
            
            #top bar (moved from top)
            window.blit(topshadow, (0, 64), special_flags=pg.BLEND_RGBA_MULT)
            window.blit(topgradient, (0, 0))
            
            if view == 0:
                window.blit(topshadow, (0, 524), special_flags=pg.BLEND_RGBA_MULT)
                window.blit(topgradient, (0, 460))
                drawshadowtext(periods[bottomtomorrow]["name"].upper(), smallmedfont, 5, 465, 5, 127)
            
            viewnames = ["Split View", "Overview", "7-Day Forecast", "Hourly Graph", f"Weather Report ({periods[0]['name']})", f"Weather Report ({periods[1]['name']})", f"Weather Report ({periods[2]['name']})", "Temperature Forecast" if not redmode else "Severe Weather Rader", "Probability of Precipitation" if not trackhurricanes else "Hurricane Tracker", "Alerts"]
            viewName = viewnames[view]
            if view == 2:
                #force view 2
                viewName = ["7-Day Forecast (Day)", "7-Day Forecast (Night)", "7-Day Forecast (Page 1)", "7-Day Forecast (Page 2)", "7-Day Forecast"][nightv]
            if wttr:
                location = smallmedfont.render(weather["nearest_area"][0]["areaName"][0]["value"], 1, (255, 255, 255, 255))
            drawshadowtext(viewName, smallmedfont, 824-312/2-smallmedfont.size(viewName)[0]/2, 5, 5, 127)
            drawshadowtext(dt.datetime.now().strftime(timeformattop), smallmedfont, 5, 5, 5, 127)
            #drawshadowtext(clock.get_fps(), smallmedfont, 5, 5, 5, 127)
            if wttr:
                drawshadowtext(weather["nearest_area"][0]["areaName"][0]["value"], smallmedfont, 1336-10-location.get_width(), 5, 5, 127)
            #drawshadowtext("Pennsylvania", smallmedfont, 1336-10-smallmedfont.size("Pennsylvania")[0], 5, 5, 127)
            
            if justswitched:
                justswitched = False
            if changetime <= 0:
                view += 1
                if view > sections:
                    view = 0
                if view == 5 and redmode:
                    view = 7
                if view == sections and len(alerts) > 0:
                    changetime = 60 * 45
                else:
                    changetime = 60 * 15
                justswitched = True
            else:
                changetime -= 60 * delta
        if scaled:
            if smoothsc:
                final.blit(pg.transform.smoothscale(window, scale), (0, 0))
            else:
                final.blit(pg.transform.scale(window, scale), (0, 0))
        pg.display.flip()
main()