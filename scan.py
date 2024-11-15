import threading as th
#import multiprocessing as mp
import requests as r
import pygame as pg
import pygame._sdl2 as sdl
import datetime as dt
from io import BytesIO
import isodate as it
import pytz as tz
import vars as varr
import json
import os
import random as rd
import time
import math
import map_tile_stitcher as ms
import map_tile_stitcher.util.conversion as msc
import geocoder as gc

print("getting variables")
sound = getattr(varr, "sound", True)
manualmusic = getattr(varr, "manualmusic", False)
ads = getattr(varr, "ads", ["Place an ad here."])
actime = getattr(varr, "adcrawltime", 4)

cachedir = os.path.dirname(os.path.abspath(__file__))

travelcities = getattr(varr, "travelcities", ["KATL", "KBOS", "KORD", "KDFW", "KDEN", "KDTW", "KLAX", "KNYC", "KMCO", "KSFO", "KSEA", "KDCA"])

performance = getattr(varr, "performance", False)
usebg = getattr(varr, "background_image_use", False)

bgimage = None
bgimager = None
if usebg:
    bgimage = pg.image.load(varr.background)
    bgimager = pg.image.load(getattr(varr, "backgroundred", varr.background))

screenwidth = 1366

tilesneededw = math.ceil(screenwidth / 256) // 2 * 2 + 1
tilesneededh = 3

loadingtasks = []

screendiff = screenwidth - 1024

transitions = True

debug = False
print(f"debug draw mode: {debug}")
def debugsleep():
    if debug:
        time.sleep(0.1)
        pg.display.flip()
        pg.event.pump()

#caches
print("making cache")
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
print("getting more options")
global scaled
scaled = getattr(varr, "scaled", False)
global scale
scale = getattr(varr, "size", (screenwidth, 768))
global smoothsc
smoothsc = getattr(varr, "smoothscale", True)

global partnered
partnered = getattr(varr, "partnered", False)
global partnerlogo
partnerlogo = getattr(varr, "logo", None)

rheaders = {
    "User-Agent": "(lewolfyt.github.io, localscope+ciblox3@gmail.com)"
}

global currentscene
currentscene = 0
#0 = main
#1 = extended travel forecast
#2 = live feed overlay

maskcolor = (255, 0, 255)
print("getting directories")
assetdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
iconf = os.path.join(assetdir, "icon.bmp")
global logo
print("loading logo")
logo = pg.image.load(iconf)
pg.display.set_icon(logo)

graphicloc = getattr(varr, "sector", "CONUS").upper()
wgraphicloc = getattr(varr, "warningsector", "CONUS").upper()
graphicwidth = getattr(varr, "graphicalwidth", 840)

#links, no touching these unless you know what you're doing
gtz = getattr(varr, "timezone", "GMT")

#TODO: figure out if what i figured out n does is correct
print("getting rank")
utn = dt.datetime.now(tz.UTC)
rankid = utn.hour
if rankid < 12:
    if rankid == 0 and utn.minute < 10:
        rank = 0
    elif rankid < 3:
        rank = 1
    elif rankid < 6:
        rank = 2
    elif rankid < 9:
        rank = 3
    else:
        rank = 4
else:
    if rankid < 12:
        rank = 0
    elif rankid < 15:
        rank = 1
    elif rankid < 18:
        rank = 2
    elif rankid < 21:
        rank = 3
    else:
        rank = 4

gtempurl = f"https://graphical.weather.gov/GraphicalNDFD.php?width={graphicwidth}&timezone={gtz}&sector={graphicloc}&element=t&n={rank}"
grainurl = f"https://graphical.weather.gov/GraphicalNDFD.php?width={graphicwidth}&timezone={gtz}&sector={graphicloc}&element=pop12&n={rank}"
warnsurl = f"https://radar.weather.gov/ridge/standard/{wgraphicloc}_0.gif"

#the todo list
#TODO: add a way to organize views
#TODO: add the hourly forecast (graph done)
#TODO: hurricane images
#TODO: make the mouse work better
#TODO: icons to show if the mouse does something

timeformat = "%I:%M %p"
timeformattop = "%I:%M:%S %p"

weatheraddr = getattr(varr, "weatheraddr", "http://wttr.in?format=j2")

musicmode = getattr(varr, "musicmode", "playlist")

playmusic = getattr(varr, "musicdir", False)

def splubby(time):
    if list(time)[0] == "0":
        return time[1:]
    else:
        return time

def lltoxy(lat, long, zoom):
    n = 2 ** zoom
    n2 = 2 ** (zoom-1)
    x = math.floor((long + 180)/360 * n)
    y = math.floor((1-(math.log(math.tan(lat * math.pi / 180) +(1/(math.cos(lat * math.pi / 180))))) / math.pi) * n2)
    return (x, y)

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
        return "Variable"
    """Converts degrees (0-360) to 16-point compass direction."""

    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

    index = round(degrees / 22.5) % 16  # Calculate index, wrap around for 360

    return directions[index]

print("initializing pygame")
pg.init()
print("done with pygame init")

if not scaled:
    print("making unscaled window")
    realwindow = pg.Window("LocalScope v1.4", (screenwidth, 768))
    realwindow.borderless = True
    window = realwindow.get_surface()
else:
    print("making fake window")
    window = pg.Surface((screenwidth, 768))
    print("making actual window")
    realwindow = pg.Window("LocalScope v1.4", scale)
    final = realwindow.get_surface()

realops = pg.Window("LocalScope - Admin Panel", (640, 480))

opswindow = realops.get_surface()

transition_s = pg.Surface((window.get_width(), window.get_height()))

print("screensaver disabled")
pg.display.set_allow_screensaver(False)

print("mouse is invisible")
pg.mouse.set_visible(False)

#print("caption set")
#pg.display.set_caption("LocalScope v1.4")
print("LocalScope v1.4 - The Worldwide Update")

if sound:
    print("loading sound")
    daytheme = pg.mixer.Sound(varr.daytheme)
    nighttheme = pg.mixer.Sound(varr.nighttheme)

def generateGradient(col1, col2, w=screenwidth, h=768, a1=255, a2=255):
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

blurmode = getattr(varr, "blurmode", "gaussian")

def blur(surf: pg.Surface, radius):
    if blurmode == "box":
        return pg.transform.box_blur(surf, radius)
    elif blurmode == "gaussian":
        return pg.transform.gaussian_blur(surf, radius)
    elif blurmode == "dropshadow":
        
        transparent = pg.Surface((surf.get_width(), surf.get_height())).convert_alpha()
        transparent.fill((255, 255, 255, 0.5))
        transparent.blit(surf, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
        
        return transparent
    else:
        return pg.Surface((1, 1))

def turnintoashadow(surf: pg.Surface, shadow=127):
    newsurf = pg.Surface((surf.get_width(), surf.get_height())).convert_alpha()
    newsurf.fill((0, 0, 0, 0))
    newsurf.blit(surf, (0, 0))
    black = pg.Surface((surf.get_width(), surf.get_height())).convert_alpha()
    black.fill((0, 0, 0, shadow))
    newsurf.blit(black, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    newsurf = blur(expandSurfaceAlpha(newsurf, 6), 4)
    return newsurf

def generateGradientHoriz(col1, col2, w=screenwidth, h=768, a1=255, a2=255):
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

apikey = varr.apikey
mapkey = varr.mapkey
unites = getattr(varr, "units", "e")

#temp unit
t = "F" if unites == "e" else "C"

#kmph?
kmp = "" if unites == "e" else "k"
kmpb = "" if unites == "e" else "K"

#pressure
pres = "inHg" if unites == "e" else "mbar"
pres_s = "in." if unites == "e" else "mbar"

#visibility
visi = "miles" if unites == "e" else "kilometers"

#precip
prec = "inches" if unites == "e" else "millimeters"

locl = getattr(varr, "locale", "en-US")

lang = {}
langf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lang", locl) + ".json"

if not os.path.exists(langf):
    langf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lang", "en-US") + ".json"

with open(langf, "r") as f:
    lang = json.loads(f.read())

tile_amounts = 20

def getWeather():
    
    global loadingstage
    global redmode
    global coords
    redmode = False
    loadingstage=0
    loadingtasks.append("Gathering initial data...")
    if True:
        if getattr(varr, "coords", False):
            coords = getattr(varr, "coords")
        else:
            templl = gc.ip("me")
            gj = templl.geojson
            coords = f'{gj["features"][0]["lat"]},{gj["features"][0]["lng"]}'
        weatherend = r.get(f'https://api.weather.gov/points/{coords}', headers=rheaders).json()
    global sunrises
    sunrises = r.get(f"https://api.sunrisesunset.io/json?lat={coords.split(',')[0]}&lng={coords.split(',')[1]}").json()
    
    zoom = 8
    basetile = msc.get_index_from_coordinate(ms.Coordinate(float(coords.split(",")[0]), float(coords.split(",")[1])), zoom)
    
    loadingstage=1
    
    global headlines
    weatherendpoint4 = f'https://api.weather.com/v3/wx/forecast/hourly/2day?geocode={coords}&units={unites}&language={locl}&format=json&format=json&apiKey={apikey}'
    observationend = f"https://api.weather.com/v3/wx/observations/current?geocode={coords}&units={unites}&language={locl}&format=json&apiKey={apikey}"
    
    global weather2 # current
    loadingstage=2
    loadingtasks.remove("Gathering initial data...")
    
    def getcc():
        global weather2
        loadingtasks.append("Retrieving current conditions...")
        weather2 = r.get(observationend).json()
        loadingtasks.remove("Retrieving current conditions...")
    th.Thread(target=getcc).start()
    
    
    global travelweathers
    global travelnames
    travelweathers = []
    travelnames = []
    def gettc():
        loadingtasks.append("Retrieving current travel conditions...")
        global travelweathers
        global travelnames
        for city in range(len(travelcities)):
            citystationinf = r.get(f'https://api.weather.com/v3/location/point?icaoCode={travelcities[city]}&language={locl}&format=json&apiKey={apikey}').json()
            cityw = r.get(f'https://api.weather.com/v3/wx/forecast/hourly/2day?icaoCode={travelcities[city]}&units={unites}&language={locl}&format=json&format=json&apiKey={apikey}').json()
            travelweathers.append(cityw)
            realname = citystationinf["location"]["displayName"]
            travelnames.append(realname)
        travelnames = getattr(vars, "travelnames", ["Atlanta", "Boston", "Chicago", "Dallas/Ft. Worth", "Denver", "Detroit", "Los Angeles", "New York City", "Orlando", "San Francisco", "Seattle", "Washington D.C."])
        loadingtasks.remove("Retrieving current travel conditions...")
    th.Thread(target=gettc).start()
    global realstationname
    def getsi():
        loadingtasks.append("Retrieving station information...")
        global realstationname
        realstationname = r.get(f'https://api.weather.com/v3/location/point?geocode={coords}&language={locl}&format=json&apiKey={apikey}').json()["location"]["city"]
        loadingtasks.remove("Retrieving station information...")
    th.Thread(target=getsi).start()
    
    global weather3 # forecast
    
    global weathericons
    global weathericonbig
    
    def getic():
        global weathericons
        global weathericonbig
        loadingtasks.append("Loading icons...")
        weathericons = [None for _ in range(22)]
    
        icdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "twc")
        icss = {}
        for image in os.listdir(icdir):
            if image == ".DS_Store":
                continue
            icss[image] = pg.image.load(os.path.join(icdir,image))
    
        global bottomtomorrowm
        for i in range(22):
            if bottomtomorrowm and i == 0:
                print("icon skipped")
                continue
            if smoothsc:
                weathericons[i] = pg.transform.smoothscale(icss[str(weather3["daypart"][0]["iconCode"][i])+".png"], (128, 128))
            else:
                weathericons[i] = pg.transform.scale(icss[str(weather3["daypart"][0]["iconCode"][i])+".png"], (128, 128))
            print(f'icon added: {weather3["daypart"][0]["iconCode"][i]}.png')
        
        if smoothsc:
            weathericonbig = pg.transform.smoothscale(icss[str(weather3["daypart"][0]["iconCode"][0+bottomtomorrowm])+".png"], (192, 192))
        else:
            weathericonbig = pg.transform.scale(icss[str(weather3["daypart"][0]["iconCode"][0+bottomtomorrowm])+".png"], (192, 192))
        loadingtasks.remove("Loading icons...")
    
    def getef():
        global weather3
        loadingtasks.append("Retrieving extended forecast...")
        weeklyend = f"https://api.weather.com/v3/wx/forecast/daily/10day?geocode={coords}&units={unites}&language={locl}&format=json&apiKey={apikey}"
        weather3 = r.get(weeklyend).json()
        global bottomtomorrowm
        bottomtomorrowm = (weather3["daypart"][0]["daypartName"][0] == None)
        loadingtasks.remove("Retrieving extended forecast...")
        th.Thread(target=getic).start()
    th.Thread(target=getef).start()
    
    global weatherraw
    def getrw():
        loadingtasks.append("Retrieving hourly forecast...")
        global weatherraw
        weatherraw = r.get(weatherendpoint4).json()
        loadingtasks.remove("Retrieving hourly forecast...")
    th.Thread(target=getrw).start()
    
    global alerts
    def getal():
        global trackhurricanes
        global redmode
        global alerts
        loadingtasks.append("Retrieving alerts...")
        alertyy = r.get(f'https://api.weather.com/v3/alerts/headlines?geocode={coords}&format=json&language={locl}&apiKey={apikey}', headers=rheaders)
        
        if alertyy.status_code not in [404, 204]:
            print("status", alertyy.status_code)
            alertyy = alertyy.json()
        else:
            alertyy = {"alerts": []}
        try:
            alerts = alertyy["alerts"]
        except:
            print(alertyy)
        global alert_details
        alert_details = []
        for alert in alerts:
            print(alert["certainty"])
            print(alert["urgency"])
            alert_details.append(
                r.get(f"https://api.weather.com/v3/alerts/detail?alertId={alert['detailKey']}&format=json&language={locl}&apiKey={apikey}").json()["alertDetail"]["texts"][0]["description"]
            )
            if not alert["certainty"] in ["Observed", "Likely"]:
                continue
            if not alert["urgency"] in ["Immediate", "Expected"]:
                continue
            redmode = True
            if "hurricane" in alert["headlineText"].lower():
                trackhurricanes = True
        loadingtasks.remove("Retrieving alerts...")
    th.Thread(target=getal).start()
    
    def getim():
        loadingtasks.append("Loading images...")
        global mappy
        global trackhurricanes
        trackhurricanes = False
        global radarimage
        radarimage = pg.image.load(BytesIO(r.get(warnsurl, headers=rheaders).content))
        global hurricaneimage
        hurricaneimage = pg.image.load(BytesIO(r.get(f"https://www.nhc.noaa.gov/xgtwo/two_{getattr(varr, 'hurricanesector', 'pac').lower()}_0d0.png", headers=rheaders).content))

        tilestart = ms.GridIndex(basetile.x - math.floor(tilesneededw/2), basetile.y - math.floor(tilesneededh/2), zoom)
        tileend = ms.GridIndex(basetile.x + math.ceil(tilesneededw/2), basetile.y + math.ceil(tilesneededh/2), zoom)

        mappy_temp = [[] for _ in range(abs(tilestart.x - tileend.x))]

        tilesneededx = list(range(tilestart.x, tileend.x+1))
        tilesneededy = list(range(tilestart.y, tileend.y+1))

        global ppa
        ppa = r.get(f"https://api.weather.com/v3/TileServer/series/productSet/PPAcore?apiKey={apikey}").json()

        global mappy_heat
        global mappy_precip
        global timestam

        #osmtiles = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        osmtiles = "https://api.mapbox.com/styles/v1/goldbblazez/ckgc8lzdz4lzh19qt7q9wbbr9/tiles/256/{z}/{x}/{y}?access_token=" + mapkey
        twctiles_heat = "https://api.weather.com/v3/TileServer/tile/twcRadarMosaic?ts={ts}&xyz={x}:{y}:{z}&apiKey=" + apikey
        # twctiles_precip = "https://api.weather.com/v3/TileServer/tile/precip24hrFcst?ts={ts}&fts={fts}&xyz={x}:{y}:{z}&apiKey=" + apikey
        twch_temp = [[[] for _ in range(tile_amounts)] for _ in range(abs(tilestart.x - tileend.x))]
        # twpc_temp = [[[] for _ in range(5)] for _ in range(abs(tilestart.x - tileend.x))]

        try:
            os.mkdir(os.path.join(cachedir, "cache"))
        except:
            pass
        
        realcache = os.path.join(cachedir, "cache")

        timestam = [[], []]
        def premap():
            for i in range(abs(tilestart.x - tileend.x)):
                for j in range(abs(tilestart.y - tileend.y)):
                    url = osmtiles.format(z=zoom, x=tilesneededx[i], y=tilesneededy[j])
                    
                    if not os.path.exists(os.path.join(realcache, f"{zoom}_{tilesneededx[i]}_{tilesneededy[j]}.png")):
                        ee = r.get(url, headers=rheaders).content
                        mappy_temp[i].append(pg.image.load(BytesIO(ee)))
                        with open(os.path.join(realcache, f"{zoom}_{tilesneededx[i]}_{tilesneededy[j]}.png"), "wb") as ff:
                            ff.write(ee)
                    else:
                        mappy_temp[i].append(pg.image.load(os.path.join(realcache, f"{zoom}_{tilesneededx[i]}_{tilesneededy[j]}.png")))
        global maphdone
        maphdone = False
        def getmaph():
            for i in range(abs(tilestart.x - tileend.x)):
                for j in range(abs(tilestart.y - tileend.y)):
                    base1 = ppa["seriesInfo"]["twcRadarMosaic"]["series"]
                    for k in range(tile_amounts):
                        twch_temp[i][k].append(None)
                        timestam[0].append(dt.datetime.fromtimestamp(base1[tile_amounts-1-k]["ts"]))
            def getmaph_sect(k):
                for i in range(abs(tilestart.x - tileend.x)):
                    for j in range(abs(tilestart.y - tileend.y)):
                        base1 = ppa["seriesInfo"]["twcRadarMosaic"]["series"]
                        ht = twctiles_heat.format(ts=base1[4-k]["ts"], z=zoom, x=tilesneededx[i], y=tilesneededy[j])
                        eh = r.get(ht, headers=rheaders).content
                        twch_temp[i][k][j] = (pg.image.load(BytesIO(eh)))
                        print("mapsect:", dt.datetime.fromtimestamp(base1[tile_amounts-1-k]["ts"]), "i", i, "j", j, "k", k)
            threads = []
            for k in range(tile_amounts):
                threads.append(th.Thread(target=getmaph_sect, args=[k]))
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            global maphdone
            maphdone = False
        # global mappdone
        # mappdone = False
        # def getmapp():
        #     for i in range(abs(tilestart.x - tileend.x)):
        #         for j in range(abs(tilestart.y - tileend.y)):
        #             base2 = ppa["seriesInfo"]["satradFcst"]["series"][0]
        #             for k in range(5):
        #                 twpc_temp[i][k].append(None)
        #                 timestam[1].append(dt.datetime.fromtimestamp(base2["fts"][-(k+1)]))
        #     def getmapp_sect(k):
        #         for i in range(abs(tilestart.x - tileend.x)):
        #             for j in range(abs(tilestart.y - tileend.y)):
        #                 base2 = ppa["seriesInfo"]["satradFcst"]["series"][0]
        #                 pc = twctiles_precip.format(ts=base2["ts"], fts=base2["fts"][-(k+1)], z=zoom, x=tilesneededx[i], y=tilesneededy[j])
        #                 ep = r.get(pc, headers=rheaders).content
        #                 twpc_temp[i][k][j] = (pg.image.load(BytesIO(ep)))
        #                 print("p ts ", dt.datetime.fromtimestamp(base2["ts"]))
        #                 print("p fts ", dt.datetime.fromtimestamp(base2["fts"][-(k+1)]))
        #                 print("mapsect:", dt.datetime.fromtimestamp(base2["fts"][-(k+1)]), "i", i, "j", j, "k", k)
            
        #     threads = []
        #     for k in range(5):
        #         threads.append(th.Thread(target=getmapp_sect, args=[k]))
        #     for thread in threads:
        #         thread.start()
        #     for thread in threads:
        #         thread.join()
        #     global mappdone
        #     mappdone = False
        
        premapt = th.Thread(target=premap)
        mapht = th.Thread(target=getmaph)
        # mappt = th.Thread(target=getmapp)
        premapt.start()
        mapht.start()
        # mappt.start()
        
        premapt.join()
        mapht.join()
        # mappt.join()
        
        print("maps done")
        mappy = pg.Surface((256 * tilesneededw, 256*tilesneededh))
        mappy_heat = [pg.Surface((256 * tilesneededw, 256*tilesneededh), flags=pg.SRCALPHA) for _ in range(tile_amounts)]
        # mappy_precip = [pg.Surface((256 * tilesneededw, 256*tilesneededh)) for _ in range(tile_amounts)]
        mappy = pg.Surface((256 * tilesneededw, 256*tilesneededh))
        for i in range(len(mappy_temp)):
            for j in range(len(mappy_temp[i])):
                mappy.blit(mappy_temp[i][j], (i*256, j*256))
                for k in range(tile_amounts):
                    mappy_heat[k].blit(twch_temp[i][k][j], (i*256, j*256))
                    # mappy_precip[k].blit(twpc_temp[i][k][j], (i*256, j*256))
        # for k in range(5):
        #     mappy_precip[k].set_alpha(round(255/6*5))
        loadingtasks.remove("Loading images...")
    th.Thread(target=getim).start()
    
    if partnered:
        loadingtasks.append("Loading your logo...")
        global logosurf
        logosurf = pg.image.load(partnerlogo)
        loadingtasks.remove("Loading your logo...")
    
    while len(loadingtasks) > 0:
        pass
    
    global loading
    loading = False

def refreshWeather():
    global loadingtext
    global loadingstage
    global redmode
    global coords
    loadingstage=0
    if True:
        if getattr(varr, "coords", False):
            coords = getattr(varr, "coords")
        else:
            templl = gc.ip("me")
            gj = templl.geojson
            coords = f'{gj["features"][0]["lat"]},{gj["features"][0]["lng"]}'
        weatherend = r.get(f'https://api.weather.gov/points/{coords}', headers=rheaders).json()
    global sunrises
    sunrises = r.get(f"https://api.sunrisesunset.io/json?lat={coords.split(',')[0]}&lng={coords.split(',')[1]}").json()
    
    forecastoffice = weatherend["properties"]["forecastOffice"]
    headlineend = forecastoffice + "/headlines"
    global headlines
    weatherendpoint3 = weatherend["properties"]["forecastHourly"]
    weatherendpoint4 = f'https://api.weather.com/v3/wx/forecast/hourly/2day?geocode={coords}&units={unites}&language={locl}&format=json&format=json&apiKey={apikey}'
    observationend = f"https://api.weather.com/v3/wx/observations/current?geocode={coords}&units={unites}&language={locl}&format=json&apiKey={apikey}"
    print(observationend)
    stationname = "Temporary"
    print(stationname)
    global weather2 # current
    weather2 = r.get(observationend).json()
    global travelweathers
    global travelnames
    travelweathers = []
    travelnames = []
    for city in range(len(travelcities)):
        citystationinf = r.get(f'https://api.weather.com/v3/location/point?icaoCode={travelcities[city]}&language={locl}&format=json&apiKey={apikey}').json()
        cityw = r.get(f'https://api.weather.com/v3/wx/forecast/hourly/2day?icaoCode={travelcities[city]}&units={unites}&language={locl}&format=json&format=json&apiKey={apikey}').json()
        travelweathers.append(cityw)
        realname = citystationinf["location"]["displayName"]
        travelnames.append(realname)
    travelnames = getattr(vars, "travelnames", ["Atlanta", "Boston", "Chicago", "Dallas/Ft. Worth", "Denver", "Detroit", "Los Angeles", "New York City", "Orlando", "San Francisco", "Seattle", "Washington D.C."])

    global realstationname
    realstationname = r.get(f'https://api.weather.com/v3/location/point?geocode={coords}&language={locl}&format=json&apiKey={apikey}').json()["location"]["city"]
    global weather3 # forecast
    weeklyend = f"https://api.weather.com/v3/wx/forecast/daily/10day?geocode={coords}&units={unites}&language={locl}&format=json&apiKey={apikey}"
    weather3 = r.get(weeklyend).json()
    global weather4
    weather4 = r.get(weatherendpoint3, headers=rheaders).json()
    global weatherraw
    weatherraw = r.get(weatherendpoint4).json()
    global alerts
    if True:
        alertyy = r.get(f'https://api.weather.com/v3/alerts/headlines?geocode={coords}&format=json&language={locl}&apiKey={apikey}', headers=rheaders)
        
        if alertyy.status_code not in [404, 204]:
            print("status", alertyy.status_code)
            alertyy = alertyy.json()
        else:
            alertyy = {"alerts": []}
        try:
            alerts = alertyy["alerts"]
        except:
            print(alertyy)
    global weathericons
    global weathericonbig
    headlines = r.get(headlineend, headers=rheaders).json()["@graph"]
    weathericons = [None for _ in range(22)]
    global bottomtomorrowm
    bottomtomorrowm = (weather3["daypart"][0]["daypartName"][0] == None)
    icdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "twc")
    icss = {}
    for image in os.listdir(icdir):
        if image == ".DS_Store":
            continue
        icss[image] = pg.image.load(os.path.join(icdir,image))
    
    for i in range(22):
        if bottomtomorrowm and i == 0:
            continue
        if smoothsc:
            weathericons[i] = pg.transform.smoothscale(icss[str(weather3["daypart"][0]["iconCode"][i])+".png"], (128, 128))
        else:
            weathericons[i] = pg.transform.scale(icss[str(weather3["daypart"][0]["iconCode"][i])+".png"], (128, 128))
        
    if smoothsc:
        weathericonbig = pg.transform.smoothscale(icss[str(weather3["daypart"][0]["iconCode"][0+bottomtomorrowm])+".png"], (192, 192))
    else:
        weathericonbig = pg.transform.scale(icss[str(weather3["daypart"][0]["iconCode"][0+bottomtomorrowm])+".png"], (192, 192))

    global mappy
    global trackhurricanes
    trackhurricanes = False
    global radarimage
    radarimage = pg.image.load(BytesIO(r.get(warnsurl, headers=rheaders).content))
    global hurricaneimage
    hurricaneimage = pg.image.load(BytesIO(r.get(f"https://www.nhc.noaa.gov/xgtwo/two_{getattr(varr, 'hurricanesector', 'pac').lower()}_0d0.png", headers=rheaders).content))
    
    
    
    global ppa
    ppa = r.get(f"https://api.weather.com/v3/TileServer/series/productSet/PPAcore?apiKey={apikey}").json()
    
    global alert_details
    alert_details = []
    for alert in alerts:
        print(alert["certainty"])
        print(alert["urgency"])
        alert_details.append(
            r.get(f"https://api.weather.com/v3/alerts/detail?alertId={alert['detailKey']}&format=json&language={locl}&apiKey={apikey}").json()["alertDetail"]["texts"][0]["description"]
        )
        if not alert["certainty"] in ["Observed", "Likely"]:
            continue
        if not alert["urgency"] in ["Immediate", "Expected"]:
            continue
        redmode = True
        if "hurricane" in alert["headlineText"].lower():
            trackhurricanes = True
    
def refreshTiles():
    print("refreshing tiles!")
    zoom = 8
    basetile = msc.get_index_from_coordinate(ms.Coordinate(float(coords.split(",")[0]), float(coords.split(",")[1])), zoom)
    
    tilestart = ms.GridIndex(basetile.x - math.floor(tilesneededw/2), basetile.y - math.floor(tilesneededh/2), zoom)
    tileend = ms.GridIndex(basetile.x + math.ceil(tilesneededw/2), basetile.y + math.ceil(tilesneededh/2), zoom)
    
    mappy_temp = [[] for _ in range(abs(tilestart.x - tileend.x))]
    
    tilesneededx = list(range(tilestart.x, tileend.x+1))
    tilesneededy = list(range(tilestart.y, tileend.y+1))
    
    global mappy_heat
    global mappy_precip
    
    #osmtiles = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    osmtiles = "https://api.mapbox.com/styles/v1/goldbblazez/ckgc8lzdz4lzh19qt7q9wbbr9/tiles/256/{z}/{x}/{y}?access_token=" + mapkey
    twctiles_heat = "https://api.weather.com/v3/TileServer/tile/twcRadarMosaic?ts={ts}&xyz={x}:{y}:{z}&apiKey=" + apikey
    # twctiles_precip = "https://api.weather.com/v3/TileServer/tile/precip24hrFcst?ts={ts}&fts={fts}&xyz={x}:{y}:{z}&apiKey=" + apikey
    twch_temp = [[[] for _ in range(tile_amounts)] for _ in range(abs(tilestart.x - tileend.x))]
    # twpc_temp = [[[] for _ in range(5)] for _ in range(abs(tilestart.x - tileend.x))]
    
    try:
        os.mkdir(os.path.join(cachedir, "cache"))
    except:
        pass
    
    realcache = os.path.join(cachedir, "cache")
    
    for i in range(abs(tilestart.x - tileend.x)):
        for j in range(abs(tilestart.y - tileend.y)):
            url = osmtiles.format(z=zoom, x=tilesneededx[i], y=tilesneededy[j])
            
            if not os.path.exists(os.path.join(realcache, f"{zoom}_{tilesneededx[i]}_{tilesneededy[j]}.png")):
                ee = r.get(url, headers=rheaders).content
                mappy_temp[i].append(pg.image.load(BytesIO(ee)))
                with open(os.path.join(realcache, f"{zoom}_{tilesneededx[i]}_{tilesneededy[j]}.png"), "wb") as ff:
                    ff.write(ee)
            else:
                mappy_temp[i].append(pg.image.load(os.path.join(realcache, f"{zoom}_{tilesneededx[i]}_{tilesneededy[j]}.png")))
            #if tilesneededx[i] == basetile.x:
            #        if tilesneededy[j] == basetile.y:
            #            pg.image.save(mappy_temp[i][-1], os.path.join(realcache, f"{zoom}_{tilesneededx[i]}_{tilesneededy[j]}_thisisit.png"))
            base1 = ppa["seriesInfo"]["twcRadarMosaic"]["series"]
            #base2 = ppa["seriesInfo"]["satradFcst"]["series"][0]
            for k in range(tile_amounts):
                ht = twctiles_heat.format(ts=base1["ts"][tile_amounts--k], z=zoom, x=tilesneededx[i], y=tilesneededy[j])
                # pc = twctiles_precip.format(ts=base2["ts"], fts=base2["fts"][-(k+1)], z=zoom, x=tilesneededx[i], y=tilesneededy[j])
                eh = r.get(ht, headers=rheaders).content
                twch_temp[i][k].append(pg.image.load(BytesIO(eh)))
                # ep = r.get(pc, headers=rheaders).content
                # twpc_temp[i][k].append(pg.image.load(BytesIO(ep)))
                timestam[0][k] = (dt.datetime.fromtimestamp(base1[tile_amounts--k]["ts"]))
                #timestam[1][k] = (dt.datetime.fromtimestamp(base2["fts"][-(k+1)]))
    
    for i in range(len(mappy_temp)):
        for j in range(len(mappy_temp[i])):
            mappy.blit(mappy_temp[i][j], (i*256, j*256))
            for k in range(tile_amounts):
                mappy_heat[k].blit(twch_temp[i][k][j], (i*256, j*256))
                # mappy_precip[k].blit(twpc_temp[i][k][j], (i*256, j*256))
    # for k in range(5):
    #     mappy_precip[k].set_alpha(round(255/6*5))

class RepeatTimer(th.Timer):
    def run(self):  
        while not self.finished.wait(self.interval):  
            self.function(*self.args,**self.kwargs)

print("making timer")
rrt = RepeatTimer(300, refreshWeather)
rrtt = RepeatTimer(300, refreshWeather)
rrt.daemon = True
rrtt.daemon = True

print("generating gradients")

gradient_c = ((0, 80, 255), (0, 180,  255))
gradient_redc = ((255, 0, 0), (255, 90, 0))
topgradient_c = ((34, 139, 34), (124, 252, 0))
topgradientred_c = ((34, 139, 34), (124, 252, 0))
bottomgradient_c = ((240, 128, 128), (178, 34, 34))
bottomgradient_redc = ((0, 80, 255), (0, 180,  255))
chartbg_c = ((0, 140, 255), (0, 40, 255))
weekbg_c = ((0, 140, 255), (0, 40, 255))
weekbg_darkc = ((140, 140, 140), (40, 40, 40))
# gradient_c = ((136,231,136), (46,111,64))
# gradient_redc = ((255, 0, 0), (255, 90, 0))
# topgradient_c = ((205,28,24), (102,0,51))
# bottomgradient_c = ((99,149,238), (39,39,87))
# bottomgradient_redc = ((136,231,136), (46,111,64))
# chartbg_c = ((136,231,136), (46,111,64))
# chartbg_darkc = ((140, 140, 140), (40, 40, 40))

if getattr(varr, "color_replace", None) != None:
    replace = getattr(varr, "color_replace", None)
    for k in list(replace.keys()):
        vars()[k] = replace[k]

gradient = generateGradient(*gradient_c)
gradientred = generateGradient(*gradient_redc)
topgradient = generateGradientHoriz(*topgradient_c, h=64)
topgradientred = generateGradientHoriz(*topgradientred_c, h=64)
bottomgradient = generateGradientHoriz(*bottomgradient_c, h=64)
bottomgradientred = generateGradientHoriz(*bottomgradient_redc, h=64)

topshadow = generateGradient((127, 127, 127), (255, 255, 255), a1=127, a2=0, h=16)
bottomshadow = generateGradient((255, 255, 255), (127, 127, 127), a1=127, a2=0, h=16)

weekbg = generateGradient(*chartbg_c, w=140, h=556)
weekbg.blit(generateGradient(*reversed(chartbg_c), w=130, h=546), (5, 5))

weekbgn = generateGradient(*weekbg_darkc, w=140, h=556)
weekbgn.blit(generateGradient(*reversed(weekbg_darkc), w=130, h=546), (5, 5))

weekbgc = generateGradient(*weekbg_c, w=140, h=276)
weekbgc.blit(generateGradient(*reversed(weekbg_c), w=130, h=266), (5, 5))

weekbgnc = generateGradient(*weekbg_darkc, w=140, h=276)
weekbgnc.blit(generateGradient(*reversed(weekbg_darkc), w=130, h=266), (5, 5))

graphbg = generateGradient(*chartbg_c, w=(994+screendiff), h=556)
graphbg.blit(generateGradient(*reversed(chartbg_c), w=(984+screendiff), h=546), (5, 5))

if getattr(varr, "image_replace", None) != None:
    replace = getattr(varr, "image_replace", None)
    for k in list(replace.keys()):
        vars()[k] = pg.image.load(replace[k])

print("done making gradients")

fontname = getattr(varr, "font", "Arial")
bold = getattr(varr, "bold", True)
sizemult = 1
if getattr(varr, "sysfont", True):
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
print("weather thread started")
rrt.start()
rrtt.start()
print("timers started (we changed the order of these functions)")

def alphablit(surf, alpha, coord):
    transparent = pg.surface.Surface((surf.get_width(), surf.get_height())).convert_alpha()
    transparent.fill((255, 255, 255, alpha))
    transparent.blit(surf, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(transparent, coord)
def alphablit2(surf, alpha, coord, dest):
    transparent = pg.surface.Surface((surf.get_width(), surf.get_height())).convert_alpha()
    transparent.fill((255, 255, 255, alpha))
    transparent.blit(surf, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    dest.blit(transparent, coord)

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

def drawshadowtext(text, size, x, y, offset, shadow=127, totala=255, wind=window):
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
    
    if totala != 255:
        usecache = False
    
    if not usecache:
        textn = size.render(text, 1, (255, 255, 255, 0))
        textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
        textsh = blur(expandSurface(textsh, 6), 4)
        
        if totala != 255:
            buf = pg.Surface((textsh.get_width(), textsh.get_height()))
            buf.fill((255, 255, 255))
            alphablit2(buf, 255-totala, (0, 0), textsh)
        
        
        if totala == 255:
            if not text in textcache:
                textcache[text] = {}
                textcache[text][size] = []
        if totala == 255:
            textcache[text][size].append(textn)
            textcache[text][size].append(textsh)
        textbland = size.render(text, 1, (255, 255, 255, 255))
        if totala == 255:
            textcache[text][size].append(textbland)
    
    if totala != 255:
        wind.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
        alphablit2(textn, totala, (x, y), wind)
    else:
        wind.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
        wind.blit(textn, (x, y))
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
        textsh = blur(expandSurface(textsh, 6), 4)
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
    if size.size(str(text))[0] > targetWidth:
        textn = pg.transform.smoothscale(textn, (targetWidth, size.size(text)[1]))
        textsh = pg.transform.smoothscale(textsh, (targetWidth, size.size(text)[1]))
    textsh = blur(expandSurface(textsh, 6), 4)
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
        textsh = blur(expandSurface(textsh, 6), 4)
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
    textsh = blur(expandSurface(textsh, 6), 4)
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
        textsh = blur(expandSurface(textsh, 6), 4)
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
        textsh = blur(expandSurface(textsh, 6), 4)
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
        time = it.parse_datetime(ti).astimezone(tz.timezone(getattr(varr, "timezone", "EST")))
        tim = length.seconds / 3600
        tim += length.days * 24
        for i in range(int(tim)):
            alltimes.append((time + dt.timedelta(hours=i)).astimezone(tz.timezone(getattr(varr, "timezone", "EST"))))
    now.replace(tzinfo=tz.timezone(getattr(varr, "timezone", "EST")))
    for time in range(len(alltimes)):
        if now.astimezone(tz.timezone(getattr(varr, "timezone", "EST"))) > alltimes[time].astimezone(tz.timezone(getattr(varr, "timezone", "EST"))):
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
    return vals[offset:]

def makehourlygraph():
    w = 984+screendiff
    h = 546
    surf = pg.Surface((w, h)).convert_alpha()
    surf2 = pg.Surface((w, h)).convert_alpha()
    
    temps = weatherraw["temperature"][0:25]
    cloud = weatherraw["cloudCover"][0:25]
    precip = weatherraw["precipChance"][0:25]
    #for val in getValuesHourly(weatherraw["properties"]["temperature"]["values"]):
    #    temps.append(round(float(val)*1.8+32))
    offset = 0
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
    
    surf2 = blur(expandSurface(surf2, 6), 4)
    
    return surf, surf2, {"mintemp": mintemp, "maxtemp": maxtemp, "medtemp": medtemp}

def trail(num):
    ln = str(num)
    if len(ln) < 2:
        return "0" + ln
    return ln

def domusic(warn=False):
    if not sound:
        return
    global music
    global shuffle
    now = dt.datetime.now()
    if not warn:
        if True:
            if True:
                if sound:
                    def egr(st):
                        if len(st) < 11:
                            return "0" + st
                    sunset = dt.datetime.strptime(egr(sunrises["results"]["sunset"]), "%I:%M:%S %p")
                    sunrise = dt.datetime.strptime(egr(sunrises["results"]["sunrise"]), "%I:%M:%S %p")
                    night = False
                    if musicmode == "playlist":
                        if not manualmusic:
                            if music == None:
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play(fade_ms=1000)
                            elif not music.get_busy():
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play(fade_ms=1000)
                            if shuffle:
                                shuffle = 0
                                music.fadeout(1000)
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play(fade_ms=1000)
                        else:
                            if music == None:
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play(-1, fade_ms=1000)
                            if shuffle:
                                shuffle = 0
                                music.fadeout(1000)
                                musicc = pg.mixer.Sound(os.path.join(playmusic, rd.choice(stripdss(os.listdir(playmusic)))))
                                music = musicc.play(-1, fade_ms=1000)
                    else:
                        global playingmusic
                        if True:
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
                            if (1 + night) != playingmusic:
                                playingmusic = 1 + night
                                if playingmusic == 1:
                                    nighttheme.fadeout(1000)
                                    daytheme.play(-1, fade_ms=1000)
                                elif playingmusic == 2:
                                    daytheme.fadeout(1000)
                                    nighttheme.play(-1, fade_ms=1000)
    else:
        if musicmode == "playlist":
            music.fadeout(1000)
        else:
            daytheme.fadeout(1000)
            nighttheme.fadeout(1000)

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

def roundd(val, precision=0):
    if val in [None, "Error"]:
        return "Error"
    else:
        return round(val, precision)

def stripdss(array: list):
    newar = array
    if ".DS_Store" in newar:
        newar.remove(".DS_Store")
    return newar

print("pumping events")
pg.event.pump()
def main():
    loadingd = 0
    bottomtomorrow = 0
    working = True
    global playingmusic
    playingmusic = 0
    view = 0
    alertscroll = 0
    alertscrollbig = 0
    alertshow = 0
    showingalert = 0
    alertdir = 1
    alerttimer = 300
    clock = pg.time.Clock()
    angl = 0
    night = False
    nightv= False
    global music
    music = None
    global shuffle
    shuffle = 0
    redded = False
    changetime = 60 * 15
    justswitched = True
    transitiontime = 0
    ticker = 0
    tickertimer = 60 * 4
    
    alerttimeout = 60 * 10
    adindex = -1
    scrollalert = False
    alerttarget = 0
    lastname = ""
    name = ""
    overridetime = 0
    
    showfps = False
    
    currentscene = 0
    #logotex = sdl.Texture.from_surface()
    #cache
    
    #currently:
    #hourlygraph
    
    
    sections = 10
    print("main loop started")
    
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
                global bottomtomorrowm
                if bottomtomorrowm:
                    if bottomtomorrow == 0:
                        bottomtomorrow = 1
                if event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == pg.BUTTON_LEFT:
                        bottomtomorrow += 1
                        if bottomtomorrow > 19:
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
                if event.key == pg.K_1:
                    currentscene = 0
                if event.key == pg.K_2:
                    currentscene = 2
                if event.key == pg.K_3:
                    currentscene = 1
                if event.key == pg.key.key_code("f"):
                    showfps = not showfps
                    overridetime = 5 * 60
                    name = "Toggled FPS View!"
                if event.key == pg.key.key_code("e"):
                    try:
                        os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "export"))
                    except:
                        pass
                    pg.image.save(gradient, os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "gradient.png"))
                    pg.image.save(gradientred, os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "gradientred.png"))
                    pg.image.save(topgradient, os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "topgradient.png"))
                    pg.image.save(topgradientred, os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "topgradientred.png"))
                    pg.image.save(bottomgradient, os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "bottomgradient.png"))
                    pg.image.save(weekbgc, os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "weekbgc.png"))
                    pg.image.save(weekbgnc, os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "weekbgnc.png"))
                    pg.image.save(graphbg, os.path.join(os.path.dirname(os.path.abspath(__file__)), "export", "graphbg.png"))
                    overridetime = 5 * 60
                    name = "Exported gradients successfully!"
        if not working:
            break
        perfit = (True if not performance else justswitched)
        if perfit:
            if not usebg:
                window.blit(gradient if not redmode else gradientred, (0, 0))
            else:
                if smoothsc:
                    window.blit(pg.transform.smoothscale(bgimage if not redmode else bgimager, (screenwidth, 768)), (0, 0))
                else:
                    window.blit(pg.transform.scale(bgimage if not redmode else bgimager, (screenwidth, 768)), (0, 0))
        if loading:
            loadingd += 0.1
            angl += 5 * math.sin(math.pi * math.sin(loadingd/10))
            lgs = pg.transform.rotozoom(logo, angl - 45, math.log(loadingd/100+0.1))
            window.blit(lgs, (screenwidth/2-lgs.get_width()/2, (768/2)-lgs.get_height()/2))
            
            loadtext = smallmedfont.render("Current tasks:\n" + "\n".join(loadingtasks), 1, (255, 255, 255, 255))
            loadshadow = smallmedfont.render("Current tasks:\n" + "\n".join(loadingtasks), 1, (0, 0, 0, 100))
            alphablit(loadshadow, 127, (5+7, 5+7))
            window.blit(loadtext, (5, 5))
        elif currentscene == 2:
            now = dt.datetime.now()
            domusic()
            obstime = dt.datetime.strptime("-".join(weather2["validTimeLocal"].split("-")[:-1]), "%Y-%m-%dT%H:%M:%S")
            #obstimetemp = obstime.replace(tzinfo=tz.utc)
            #obstimetemp = obstimetemp.astimezone(tz.timezone(getattr(varr, "timezone", "UTC")))
            #obstimeshort = splubby(obstimetemp.strftime("%I:%M %p"))
            obstimeshort = splubby(obstime.strftime("%I:%M %p"))
            currenttime = splubby(now.strftime("%I:%M:%S %p"))
            currentdate = now.strftime("%a %b ") + splubby(now.strftime("%d"))
            window.fill(maskcolor)
            window.blit(bottomgradientred if not redmode else bottomgradient, (0, 704-64))
            window.blit(bottomgradientred if not redmode else bottomgradient, (0, 704))

            if len(alerts) > 0:
                if len(alerts) > 1:
                    if alerttimer > 0:
                        alerttimer -= 1 * delta * 60
                    else:
                        if performance:
                            alertscroll = screenwidth
                        else:
                            alertscroll += 5 * delta * 60
                if alertscroll > screenwidth:
                    showingalert += 1
                    alertscroll = 0
                    alerttimer = 300
                    if showingalert > len(alerts)-1:
                        showingalert = 0
                if len(alerts) > 1:
                    drawshadowcrunchcol(alerts[(showingalert+1) if showingalert != len(alerts)-1 else 0]["headlineText"], (255, 0, 0) if not redmode else (0, 127, 255), smallmedfont, -1019 + alertscroll, 80, 5, 1024-15, 127)
            else:
                drawshadowtext(currentdate, smallmedfont, 5, 704-64+5, 5, 127)
                drawshadowtext(currenttime, smallmedfont, screenwidth - 5 - smallmedfont.size(currenttime)[0], 704-64+5, 5, 127)
            
            if tickertimer <= 0:
                ticker += 1
                if ticker > 6:
                    ticker = 0
                if ticker == 6:
                    adindex += 1
                    if adindex > len(ads)-1:
                        adindex = 0
                    tickertimer = 60 * actime
                else:
                    tickertimer = 60 * 4
            else:
                tickertimer -= 60 * delta
            
            tickerright = ""
            if ticker == 0:
                tickername = f'Last updated at {obstimeshort}'
                tickername = f'Current conditions for {realstationname}'
            elif ticker == 1:
                tickername = f'{lang["temp"]}: {round(weather2["temperature"])}°{t}'
                tickerright = f'{lang["feels"]}: {round(weather2["temperatureFeelsLike"])}°{t}'
            elif ticker == 2:
                tickername = f'{lang["humid"]}: {roundd(weather2["relativeHumidity"])}%'
                tickerright = f'{lang["uv"]}: {round(weather2["uvIndex"])}'
            elif ticker == 3:
                pressa = ["(-)", "(+)", "(-)", "(++)", "(--)"]
                tickername = f'{lang["pressure"]}: {round(weather2["pressureAltimeter"], 2)} {pres_s} {pressa[weather2["pressureTendencyCode"]]}'
            elif ticker == 4:
                if weather2["windDirectionCardinal"] != "CALM":
                    tickername = f'{lang["wind"]}: {weather2["windDirectionCardinal"]} @ {round(weather2["windSpeed"])} {kmp}mph'
                else:
                    tickername = f"{lang['wind']}: {lang['calm']}"
                if weather2["windGust"]:
                    tickerright = f"{lang['gusts']}: {weather2['windGust']}"
            elif ticker == 5:
                try:
                    ceiling = nonezero(weather2["cloudCeiling"])
                except IndexError:
                    ceiling = 0
                tickername = f'{lang["visib"]}: {round(weather2["visibility"])} {visi}'
                tickerright = f'{lang["ceil"]}: {"Unlimited" if ceiling == 0 else f"{ceiling} feet"}'
            elif ticker == 6:
                tickername = ads[adindex]
            drawshadowtext(tickername, smallmedfont, 5, 768-64+5, 5, 127)
            drawshadowtext(tickerright, smallmedfont, screenwidth-5-smallmedfont.size(tickerright)[0], 768-64+5, 5, 127)
        else:
            if not redded:
                if redmode:
                    view = sections
                    changetime = 60 * 30
                redded = True
            domusic()
            periods = weather3["daypart"][0]
            currenttemp = giganticfont.render(f'{trail(round(weather2["temperature"]))}', 1, (255, 255, 255, 255))
            currentcondition = smallmedfont.render(weather2["wxPhraseLong"], 1, (255, 255, 255, 255))
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
            # drawshadowtext(viewName, smallmedfont, 824-screendiff/2-smallmedfont.size(viewName)[0]/2, 5, 5, 127)
            # drawshadowtext(dt.datetime.now().strftime(timeformattop), smallmedfont, 5, 5, 5, 127)
            # #drawshadowtext(clock.get_fps(), smallmedfont, 5, 5, 5, 127)
            # if wttr:
            #     drawshadowtext(weather["nearest_area"][0]["areaName"][0]["value"], smallmedfont, screenwidth-10-location.get_width(), 5, 5, 127)
            
            #today
            # today's forecast (min, axg, max) (deprecated)
            #drawshadowtemp("Previous 24h extremes:", smallmedfont, 5, 80, 5, 127)
            #drawshadowtempcol(round(formatMetric(weather2["features"][0]["properties"]["minTemperatureLast24Hours"])), (135, 206, 250, 255), smallmedfont,405, 80, 5, 127)
            #drawshadowtempcol(round(formatMetric(weather2["features"][0]["properties"]["maxTemperatureLast24Hours"])), (255, 140, 0, 255), smallmedfont, 480, 80, 5, 127)
            # alerts
            if view != sections and (True if not performance else justswitched):
                if len(alerts) > 0:
                    if len(alerts) > 1:
                        if alerttimer > 0:
                            alerttimer -= 1 * delta * 60
                        else:
                            if performance:
                                alertscroll = screenwidth
                            else:
                                alertscroll += 5 * delta * 60
                    if alertscroll > screenwidth:
                        showingalert += 1
                        alertscroll = 0
                        alerttimer = 300
                        if showingalert > len(alerts)-1:
                            showingalert = 0
                    if not redmode:
                        drawshadowcrunchcol(alerts[showingalert]["headlineText"], (255, 0, 0), smallmedfont, 5 + alertscroll, 80, 5, screenwidth-15, 127)
                    else:
                        drawshadowcrunchcol(alerts[showingalert]["headlineText"], (0, 127, 255), smallmedfont, 5 + alertscroll, 80, 5, screenwidth-15, 127)
                    if len(alerts) > 1:
                        drawshadowcrunchcol(alerts[(showingalert+1) if showingalert != len(alerts)-1 else 0]["headlineText"], (255, 0, 0), smallmedfont, -1019 + alertscroll, 80, 5, 1024-15, 127)
                else:
                    drawshadowtext(lang["noalert"], smallmedfont, 5, 80, 5, 127)
            # current
            
            perfit = (True if not performance else justswitched)
            
            if view in [0, 1] and perfit:
                precip = weather2["precip1Hour"]
                if precip == None:
                    precip = "0"
                else:
                    precip = str(round(precip/25.4, 1))
                currenttemp = drawshadowtemp(trail(round(weather2["temperature"])), giganticfont, 60, 80, 20, 180)
                drawshadowtext(f"°{t}", bigfont, currenttemp.get_width()+60, 125, 10, 160)
                if weather2["windDirectionCardinal"] != "CALM":
                    #print(weather2["features"][0]["properties"]["windSpeed"])
                    drawshadowtext(f'{lang["wind"]}: {weather2["windDirectionCardinal"]} @ {round((weather2["windSpeed"]))} {kmpb}MPH', smallmedfont, 540, 125, 5, 127)
                else:
                    drawshadowtext(f'{lang["wind"]}: {lang["calm"]}', smallmedfont, 540, 125, 5, 127)
                drawshadowtext(f'{lang["relhumid"]}: {roundd(weather2["relativeHumidity"], 1)}%', smallmedfont, 540, 175, 5, 127)
                drawshadowtext(f'{lang["precip"]}: {precip} {prec}', smallmedfont, 540, 225, 5, 127)
                drawshadowtext(f'{lang["visib"]}: {round(weather2["visibility"], 1)} {visi}', smallmedfont, 540, 275, 5, 127)
                drawshadowtext(f'{lang["feels"]}: {round(weather2["temperatureFeelsLike"])}°{t}', smallmedfont, 540, 325, 5, 127)
                
                pressa = ["(-)", "(+)", "(-)", "(++)", "(--)"]
                
                drawshadowtext(f'{lang["pressure"]}: {roundd(weather2["pressureAltimeter"], 2)} {pres} {pressa[weather2["pressureTendencyCode"]]}', smallmedfont, 540, 375, 5, 127)
                #window.blit(currenttemp, (60, 80))
                offsetw = -currentcondition.get_width()/2
                if offsetw < -220:
                    offsetw = -220
                
                drawshadowcrunch(weather2["wxPhraseLong"], smallmedfont, 60+currenttemp.get_width()/2+offsetw, 400, 5, 440, 127)
                
                periods = weather3["daypart"][0]
                if bottomtomorrow == 0 and bottomtomorrowm:
                    bottomtomorrow = 1
                if view == 0:
                    #tomorrow
                    # forecasted temps
                    tm1 = drawshadowtemp(trail(periods["temperature"][bottomtomorrow]), bigfont, 60, 560, 10, 140)
                    #tm2 = drawshadowtempcol(periods["temperatureMin"][bottomtomorrow], (135, 206, 250), medfont, 280, 540, 7, 127)
                    #tm3 = drawshadowtempcol(periods["temperatureMax"][bottomtomorrow], (255, 140, 0), medfont, 280, 610, 7, 127)
                    drawshadowtext(f"°{t}", bigfont, tm1.get_width()+60, 560, 10, 140)
                    #drawshadowtextcol(f"°{t}", (135, 206, 250, 255), medfont, tm2.get_width()+280, 540, 10, 140)
                    #drawshadowtextcol(f"°{t}", (255, 140, 0, 255), medfont, tm3.get_width()+280, 610, 10, 140)
                    buffer = pg.Surface((128, 128))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 128, 128))
                    buffer = blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (tm1.get_width() + 190, 560), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(weathericons[bottomtomorrow], (tm1.get_width() + 180, 550))
                    # other metrics
                    prval = periods["precipChance"][bottomtomorrow]
                    if prval == None:
                        prval = "0"
                    drawshadowtext(f'{lang["precipchance"]}: {prval}%', smallmedfont, 440, 540, 5, 127)
                    drawshadowtext(f'{lang["wind"]}: {periods["windDirectionCardinal"][bottomtomorrow]} @ {periods["windSpeed"][bottomtomorrow]}', smallmedfont, 440, 590, 5, 127)
                    drawshadowcrunch(periods["wxPhraseLong"][bottomtomorrow], smallmedfont, 440, 640, 5, screenwidth-440-10, 127)
                else:
                    drawshadowtext("\n".join(wraptext(periods["narrative"][bottomtomorrow], pg.Rect(350, 480, screenwidth-350-15, 768-64-15), smallishfont)), smallishfont, 350, 480, 5, 127)
                    buffer = pg.Surface((192, 192))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 192, 192))
                    buffer = blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (110, 490), special_flags=pg.BLEND_RGBA_MULT)
                    if weathericonbig != None:
                        window.blit(weathericonbig, (100, 480))
            elif view == 2 and perfit:
                nightv = 4
                nowisday = (periods["dayOrNight"][0] == "D")
                if nightv <= 1:
                    for i in range(7):
                        buffer = pg.Surface((140, 556))
                        pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 140, 556))
                        buffer = blur(expandSurface(buffer, 6), 4)
                        window.blit(buffer, (20 + i*142, 133), special_flags=pg.BLEND_RGBA_MULT)
                        window.blit(weekbg if not nightv else weekbgn, (15 + i*142, 128))
                        if nowisday and i == 0:
                            continue
                        if not nowisday and i == 6 and nightv:
                            continue
                        drawshadowtext(periods[i*2+(not nowisday)+nightv]["name"][0:3].upper(), smallmedfont, 15+i*142+70-smallmedfont.size(periods[i*2+(not nowisday)+nightv]["name"][0:3].upper())[0]/2, 138, 5, 127)
                        drawshadowtemp(periods[i*2+(not nowisday)+nightv]["temperature"], bigfont, 30 + i*142, 168, 5, 127)
                        drawshadowtext(f"{lang['wind']}:", smallishfont, 40 + i*142, 300, 5, 127)
                        drawshadowtext(periods[i*2+(not nowisday)+nightv]["windDirection"], medfont, 85+i*142-medfont.size(periods[i*2+(not nowisday)+nightv]["windDirection"])[0]/2, 330, 5, 127)
                        window.blit(weathericons[i*2+(not nowisday)+nightv], (21+142*i, 417+128+5))
                elif nightv <= 3:
                    for i in range(7):
                        buffer = pg.Surface((140, 556))
                        pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 140, 556))
                        buffer = blur(expandSurface(buffer, 6), 4)
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
                        drawshadowtext(f"{lang['wind']}:", smallishfont, 40 + i*142, 300, 5, 127)
                        drawshadowtext(periods[i+offset+(nightv-2)*7]["windDirection"], medfont, 85+i*142-medfont.size(periods[i+offset+(nightv-2)*7]["windDirection"])[0]/2, 330, 5, 127)
                        window.blit(weathericons[i+offset+(nightv-2)*7], (21+142*i, 417+128+5))
                else:
                    if justswitched and "7daybuffer" not in cache:
                        buffer = pg.Surface((140, 276))
                        pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 140, 276))
                        buffer = blur(expandSurface(buffer, 6), 4)
                        cache["7daybuffer"] = buffer
                    else:
                        buffer = cache["7daybuffer"]
                    if partnered:
                        if justswitched and "logoshadow" not in cache:
                            logosh = turnintoashadow(logosurf)
                            cache["logoshadow"] = logosh
                        else:
                            logosh = cache["logoshadow"]
                    exfm = getattr(varr, "extendedfamount", 18)
                    for j in range(exfm):
                        i = j/2
                        drawingn = (periods["dayOrNight"][j] == "N")
                        #if nowisday and i == 0:
                        #    continue
                        #if not nowisday and i == 6 and drawingn:
                        #    continue
                        sind = 0
                        if periods["daypartName"] == None:
                            sind += 1
                        else:
                            sind += 2
                        ind = (j + sind)
                        
                        off = -142-71+71*(20-exfm)/2 + 78 * nowisday
                        
                        if drawingn:
                            off -= 71
                        
                        scrh = screendiff/2 + off
                        
                        window.blit(buffer, (20 + scrh + i*142 - scrh*partnered - 78 * nowisday, 133+280*drawingn), special_flags=pg.BLEND_RGBA_MULT)
                        window.blit(weekbgc if not drawingn else weekbgnc, (15 + scrh + i*142 - scrh*partnered - 78 * nowisday, 128+280*drawingn))
                        drawshadowtext(weather3["dayOfWeek"][math.floor(j/2+sind/2)][0:(3 if locl != "de-DE" else 2)].upper(), smallmedfont, 15+ scrh +i*142 - 78 * nowisday - scrh*partnered+70-smallmedfont.size(weather3["dayOfWeek"][math.floor(j/2+sind/2)][0:(3 if locl != "de-DE" else 2)].upper())[0]/2, 138+280*drawingn, 5, 127)
                        drawshadowtemp(trail(periods["temperature"][ind]), medfont, 85 - 78 * nowisday - medfont.size(trail(str(periods["temperature"][ind])))[0]/2 + scrh - scrh*partnered + i*142, 172+280*drawingn, 5, 127)
                        if weathericons[ind] != None:
                            window.blit(weathericons[ind], (21+ scrh +142*i - 78 * nowisday - scrh*partnered, 417+128+5-280*(not drawingn)))
                        drawshadowtext(f'{lang["wind"]}: {periods["windDirectionCardinal"][ind]}', smallfont, 84+ scrh - 78 * nowisday - scrh*partnered +i*142-smallfont.size(f'{lang["wind"]}: {periods["windDirectionCardinal"][ind]}')[0]/2, 234+280*drawingn, 5, 127)
                    #if partnered:
                    #    window.blit(turnintoashadow(logosurf), (20 - 39 * nowisday + 142 * 7, 138))
                    #    window.blit(logosurf, (15 - 39 * nowisday + 142 * 7, 133))
            elif view == 3 and perfit:
                drawshadowtext("\n".join(wraptext("Unimplemented! If you want to see this, wait for the official update!", pg.Rect(5, 5, 1356, 768-128-64), medfont)), medfont, 5, 133, 5)
                for i in range(24):
                    pass
            elif view == 4 and perfit:
                if justswitched:
                    g, gs, vs = makehourlygraph()
                    
                    buffer = pg.Surface((994+screendiff, 556))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 994+screendiff, 556))
                    buffer = blur(expandSurface(buffer, 6), 4)
                    
                    cache["hourlybuffer"] = buffer
                    cache["hourlygraph"] = [g, gs, vs]
                    justswitched = False
                else:
                    g, gs, vs = cache["hourlygraph"]
                    buffer = cache["hourlybuffer"]
                
                window.blit(buffer, (20, 133), special_flags=pg.BLEND_RGBA_MULT)
                window.blit(graphbg, (15, 128))
                window.blit(gs, (20, 133), special_flags=pg.BLEND_RGBA_MULT)
                window.blit(g, (20, 133))
                now = dt.datetime.fromtimestamp(weatherraw["validTimeUtc"][0])
                now6 = dt.datetime.fromtimestamp(weatherraw["validTimeUtc"][0]) + dt.timedelta(hours=6)
                now12 = dt.datetime.fromtimestamp(weatherraw["validTimeUtc"][0]) + dt.timedelta(hours=12)
                now18= dt.datetime.fromtimestamp(weatherraw["validTimeUtc"][0]) + dt.timedelta(hours=18)
                now24 = dt.datetime.fromtimestamp(weatherraw["validTimeUtc"][0]) + dt.timedelta(hours=24)
                time1 = splubby(now.strftime("%I")) + ("AM" if (now.strftime("%p") == "AM") else "PM")
                time2 = splubby(now6.strftime("%I")) + ("AM" if (now6.strftime("%p") == "AM") else "PM")
                time3 = splubby(now12.strftime("%I")) + ("AM" if (now12.strftime("%p") == "AM") else "PM")
                time4 = splubby(now18.strftime("%I")) + ("AM" if (now18.strftime("%p") == "AM") else "PM")
                time5 = splubby(now24.strftime("%I")) + ("AM" if (now24.strftime("%p") == "AM") else "PM")
                drawshadowtext(f'{round(vs["maxtemp"])}°', smallmedfont, 20, 128, 5)
                drawshadowtext(f'{round(vs["medtemp"])}°', smallmedfont, 20, 128+440/2, 5)
                drawshadowtext(f'{round(vs["mintemp"])}°', smallmedfont, 20, 128+440, 5)
                drawshadowtext(time1, smallmedfont, 20, 128+500, 5)
                drawshadowtext(time2, smallmedfont, (screenwidth-640+530)/4 + 15, 128+500, 5)
                drawshadowtext(time3, smallmedfont, (screenwidth-640+530)/2 + 10, 128+500, 5)
                drawshadowtext(time4, smallmedfont, (screenwidth-640+530)*3/4 + 5, 128+500, 5)
                drawshadowtext(time5, smallmedfont, screenwidth-640+530, 128+500, 5)
                drawshadowtextcol(f"{lang['temp']}", (255, 0, 0), smallmedfont, screenwidth-16-smallmedfont.size(f"{lang['temp']}")[0], 128, 5, 127)
                drawshadowtextcol(f"{lang['precip']} %", (0, 255, 255), smallmedfont, screenwidth-16-smallmedfont.size(f"{lang['precip']} %")[0], 168, 5, 127)
                drawshadowtextcol(f"{lang['relhumidshort']} %", (255, 127, 0), smallmedfont, screenwidth-16-smallmedfont.size(f"{lang['relhumidshort']} %")[0], 208, 5, 127)
            elif view == 5 and perfit:
                for city in range(len(travelcities)):
                    drawshadowtext(travelnames[city], smallmedfont, 5, 130 + city*45, 5)
                    temps = []
                    err = False 
                    try:
                        for temp in travelweathers[city]["temperature"]:
                            temps.append(temp)
                    except:
                        err = True
                        temps = [0, 1000000]
                    lowt = min(temps)
                    hight = max(temps)
                    if not err:
                        drawshadowtempcol(f'Low: {lowt}°{t}', (135, 206, 235), smallmedfont, screenwidth - 550, 130 + city*45, 5)
                        drawshadowtextcol(f'High: {hight}°{t}', (255, 140, 0), smallmedfont, screenwidth - 250, 130 + city*45, 5)
                    else:
                        drawshadowtempcol(f'Data Error', (255, 0, 0), smallmedfont, screenwidth - 550, 130 + city*45, 5)
            elif view == 6 and perfit:
                drawshadowbigcrunch("\n".join(wraptext(f'{periods["daypartName"][0+bottomtomorrowm]}...{periods["narrative"][0+bottomtomorrowm]}', pg.Rect(15, 128, 994+screendiff, 588+32), smallmedfont)), (255, 255, 255), smallmedfont, 15, 128, 5, 994+screendiff, 588+32, 127)
            elif view == 7 and perfit:
                drawshadowbigcrunch("\n".join(wraptext(f'{periods["daypartName"][1+bottomtomorrowm]}...{periods["narrative"][1+bottomtomorrowm]}', pg.Rect(15, 128, 994+screendiff, 588+32), smallmedfont)), (255, 255, 255), smallmedfont, 15, 128, 5, 994+screendiff, 588+32, 127)
            elif view == 8 and perfit:
                drawshadowbigcrunch("\n".join(wraptext(f'{periods["daypartName"][2+bottomtomorrowm]}...{periods["narrative"][2+bottomtomorrowm]}', pg.Rect(15, 128, 994+screendiff, 588+32), smallmedfont)), (255, 255, 255), smallmedfont, 15, 128, 5, 994+screendiff, 588+32, 127)
            elif view == 9 and perfit:
                if justswitched:
                    changetime = 30 * 60
                mappyind = -(math.floor(changetime / 30) % 20 + 1)
                if True: #temp
                    window.blit(mappy, (screenwidth/2-mappy.get_width()/2, 800/2-mappy.get_height()/2))
                    window.blit(mappy_heat[mappyind], (screenwidth/2-mappy_heat[mappyind].get_width()/2, 800/2-mappy_heat[mappyind].get_height()/2))
                    drawshadowtext(timestam[0][mappyind].__str__(), smallishfont, 5, 70, 5)
                else:
                    buffer = pg.Surface((radarimage.get_width(), radarimage.get_height()))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, radarimage.get_width(), radarimage.get_height()))
                    buffer = blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (screenwidth/2-radarimage.get_width()/2+5, 800/2-radarimage.get_height()/2+5), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(radarimage, (screenwidth/2-radarimage.get_width()/2, 800/2-radarimage.get_height()/2))
            elif view == 10:
                if justswitched:
                    alertscrollbig = 0
                    alerttimeout = 60 * 10
                scrollalert = False
                if len(alerts) > 0:
                    fnt = smallmedfont
                    if getcrunch(alert_details[alertshow], smallmedfont, 994+screendiff, 588)[0] < 1:
                        fnt = smallishfont
                        if getcrunch(alert_details[alertshow], smallishfont, 994+screendiff, 588)[1] < 0.75:
                            scrollalert = True
                            alerttarget = getcrunch(alert_details[alertshow], smallishfont, 994+screendiff, 588)[3] + 5 - 588
                    elif getcrunch(alert_details[alertshow], smallmedfont, 994+screendiff, 588)[1] < 0.75:
                        fnt = smallishfont
                        if getcrunch(alert_details[alertshow], smallishfont, 994+screendiff, 588)[1] < 0.75:
                            scrollalert = True
                            alerttarget = getcrunch(alert_details[alertshow], smallfont, 994+screendiff, 588)[3] + 5 - 588
                    
                    if alerttimeout <= 0:
                        if scrollalert:
                            if performance:
                                if alertdir == 1:
                                    if len(alerts) > 1:
                                        alertshow += 1
                                        if alertshow > len(alerts)-1:
                                            view = 0
                                            justswitched = 1
                                            changetime = 60 * 15
                                        else:
                                            changetime = 60 * 30
                                    if alertscrollbig < alerttarget:
                                        alertscrollbig += 300
                                        alerttimeout = 60 * 5
                                    elif alertscrollbig >= alerttarget:
                                        alertscrollbig = 0
                                        alertdir = -1
                                        alerttimeout = 60 * 10
                                else:
                                    if alertscrollbig > 0:
                                        alertscrollbig -= 300
                                        alerttimeout = 60 * 5
                                        if alertscrollbig <= 0:
                                            alertscrollbig = 0
                                            alerttimeout = 60 * 10
                                            alertdir = 1
                                    else:
                                        alertscrollbig = 0
                                        alerttimeout = 60 * 10
                                        alertdir = 1
                            else:
                                if alertdir == 1:
                                    if len(alerts) > 1:
                                        alertshow += 1
                                        if alertshow > len(alerts)-1:
                                            view = 0
                                            justswitched = 1
                                            changetime = 60 * 15
                                        else:
                                            changetime = 60 * 30
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
                        drawshadowbigcrunch(alert_details[alertshow], (255, 224, 224), fnt, 15, 96-alertscrollbig, 5, 994+screendiff, 9999, 127)
                    else:
                        alertscroll = 0
                        drawshadowbigcrunch(alert_details[alertshow], (255, 224, 224), fnt, 15, 96, 5, 994+screendiff, 588, 127)
                else:
                    drawshadowtext(lang["noalertshort"], smallmedfont, 15, 96, 5, 127)
            #housekeeping
            realbotg = (bottomgradient if not redmode else bottomgradientred)
            window.blit(realbotg, (0, 768-realbotg.get_height()))
            
            if tickertimer <= 0:
                ticker += 1
                if ticker > 6:
                    ticker = 0
                if ticker == 6:
                    adindex += 1
                    if adindex > len(ads)-1:
                        adindex = 0
                    tickertimer = 60 * actime
                else:
                    tickertimer = 60 * 4
            else:
                tickertimer -= 60 * delta
            
            tickerright = ""
            obstime = dt.datetime.strptime("-".join(weather2["validTimeLocal"].split("-")[:-1]), "%Y-%m-%dT%H:%M:%S")
            obstimeshort = splubby(obstime.strftime("%I:%M %p"))
            if ticker == 0:
                tickername = f'Last updated at {obstimeshort}'
            elif ticker == 1:
                tickername = f'{lang["temp"]}: {round(weather2["temperature"])}°{t}'
                tickerright = f'{lang["feels"]}: {round(weather2["temperatureFeelsLike"])}°{t}'
            elif ticker == 2:
                tickername = f'{lang["humid"]}: {roundd(weather2["relativeHumidity"])}%'
                tickerright = f'{lang["uv"]}: {round(weather2["uvIndex"])}'
            elif ticker == 3:
                pressa = ["(-)", "(+)", "(-)", "(++)", "(--)"]
                tickername = f'{lang["pressure"]}: {round(weather2["pressureAltimeter"], 2)} {pres_s} {pressa[weather2["pressureTendencyCode"]]}'
            elif ticker == 4:
                if weather2["windDirectionCardinal"] != "CALM":
                    tickername = f'{lang["wind"]}: {weather2["windDirectionCardinal"]} @ {round(weather2["windSpeed"])} {kmp}mph'
                else:
                    tickername = f"{lang['wind']}: {lang['calm']}"
                if weather2["windGust"]:
                    tickerright = f"{lang['gusts']}: {weather2['windGust']} {kmp}mph"
            elif ticker == 5:
                try:
                    ceiling = nonezero(weather2["cloudCeiling"])
                except IndexError:
                    ceiling = 0
                tickername = f'{lang["visib"]}: {round(weather2["visibility"])} {visi}'
                tickerright = f'{lang["ceil"]}: {"Unlimited" if ceiling == 0 else f"{ceiling} feet"}'
            elif ticker == 6:
                tickername = ads[adindex]
            drawshadowtext(tickername, smallmedfont, 5, 768-64+5, 5, 127)
            drawshadowtext(tickerright, smallmedfont, screenwidth-5-smallmedfont.size(tickerright)[0], 768-64+5, 5, 127)
            if perfit:
                window.blit(bottomshadow, (0, 768-realbotg.get_height()-bottomshadow.get_height()), special_flags=pg.BLEND_RGBA_MULT)
            
            #top bar (moved from top)
            if perfit:
                window.blit(topshadow, (0, 64), special_flags=pg.BLEND_RGBA_MULT)
            window.blit(topgradient if not redmode else topgradientred, (0, 0))
            
            if perfit:
                if view == 0:
                    window.blit(topshadow, (0, 524), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(topgradient if not redmode else topgradientred, (0, 460))
                    if bottomtomorrowm:
                        if bottomtomorrow == 0:
                            bottomtomorrow = 1
                    drawshadowtext(periods["daypartName"][bottomtomorrow], smallmedfont, 5, 465, 5, 127)
            
            #viewnames = ["Split View", "Overview", "Extended Forecast", "Hourly Graph", "Travel Cities", f"Weather Report ({periods['daypartName'][0+bottomtomorrowm]})", f"Weather Report ({periods['daypartName'][1+bottomtomorrowm]})", f"Weather Report ({periods['daypartName'][2+bottomtomorrowm]})", "Satellite/Radar Forecast" if not redmode else "Severe Weather Rader", "Probability of Precipitation" if not trackhurricanes else "Hurricane Tracker", "Forecast Office Headlines", "Alerts"]
            viewnames = lang["viewnames"] if not redmode else lang["viewnamesred"]
            viewName = viewnames[view].replace("$1", periods['daypartName'][0+bottomtomorrowm]).replace("$2", periods['daypartName'][1+bottomtomorrowm]).replace("$3", periods['daypartName'][2+bottomtomorrowm])
            
            #if view == 2:
            #    #force view 2
            #    viewName = ["7-Day Forecast (Day)", "7-Day Forecast (Night)", "7-Day Forecast (Page 1)", "7-Day Forecast (Page 2)", "Extended Forecast"][nightv]
            
            if overridetime > 0:
                overridetime -= 60 * delta
                viewName = name
            if transitiontime == 0:
                drawshadowtext(viewName, smallmedfont, screenwidth/2-smallmedfont.size(viewName)[0]/2, 5, 5, 127)
            else:
                drawshadowtext(viewName, smallmedfont, screenwidth/2-smallmedfont.size(viewName)[0]/2, 5, 5, 127, round(255-transitiontime*255/60))
                drawshadowtext(lastname, smallmedfont, screenwidth/2-smallmedfont.size(lastname)[0]/2, 5, 5, 127, round(transitiontime*255/60))
            
            if showfps:
                drawshadowtext(round(clock.get_fps()), smallmedfont, 5, 5, 5, 127)
            else:
                drawshadowtext(splubby(dt.datetime.now().strftime(timeformattop)), smallmedfont, 5, 5, 5, 127)
            
            drawshadowtext(realstationname, smallmedfont, screenwidth-10-smallmedfont.size(realstationname)[0], 5, 5, 127)
            #drawshadowtext("Pennsylvania", smallmedfont, screenwidth-10-smallmedfont.size("Pennsylvania")[0], 5, 5, 127)
            
            if justswitched:
                justswitched = False
            if changetime <= 0:
                lastname = viewName[::][::]
                view += 1
                if view > sections:
                    view = 0
                if view == 6 and redmode:
                    view = 8
                if view == sections and len(alerts) > 0:
                    changetime = 60 * 45
                else:
                    changetime = 60 * 15
                justswitched = True
                transitiontime = 60
                transition_s = window.copy()
            else:
                changetime -= 60 * delta
        if transitiontime > 0 and not performance:
            transitiontime -= 1
            transition_s.set_alpha(round(transitiontime*255/60))
            window.blit(transition_s, (0, 65), pg.Rect(0, 65, screenwidth, 768-65-65))
        if scaled:
            if smoothsc:
                final.blit(pg.transform.smoothscale(window, scale), (0, 0))
            else:
                final.blit(pg.transform.scale(window, scale), (0, 0))
        opswindow.fill((0, 130, 255))
        drawshadowtext("Admin Panel", smallmedfont, 5, 5, 5, wind=opswindow)
        realwindow.flip()
        realops.flip()

if not getattr(pg, "IS_CE", False):
    raise ModuleNotFoundError("Pygame CE is required for this application! Please uninstall Pygame and install Pygame CE instead.")

try:
    main()
except Exception as err:
    print(err.__repr__())
    work = True
    while work:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                work = False
        window.blit(gradientred, (0, 0))
        drawshadowtext(err.__repr__(), smallfont, 15, 15, 5)
        realwindow.flip()