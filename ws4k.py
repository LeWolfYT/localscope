import threading as th
import requests as r
import pygame as pg
import datetime as dt
from io import BytesIO
from datetime import datetime as dt
from datetime import timedelta as td
import vars
import os
import pytz as tz
import PIL.Image as img
import isodate as it
import random as rd

rheaders = {
    "User-Agent": "(lewolfyt.github.io, ciblox3+myweatherstation@gmail.com)"
}

playmusic = getattr(vars, "musicdir", False)
playmusicv = (playmusic != False)

forcecoords = getattr(vars, "forcecoords", False)

#MASSIVE credits to the people who programmed ws4kp and made the assets.
assetdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
bgassetsp = os.path.join(assetdir, "bg")
currentassetsp = os.path.join(assetdir, "current")
regionalassetsp = os.path.join(assetdir, "regional")
extendedassetsp = os.path.join(assetdir, "extended")
miscassetsp = os.path.join(assetdir, "misc") #things like the logo
moonassetsp = os.path.join(assetdir, "moon") #almanac, will implement later
fontassetsp = os.path.join(assetdir, "font")

def zeropad(vl):
    if len(str(vl)) == 2:
        return vl
    if len(str(vl)) == 1:
        return "0" + str(vl)

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

def preload(dir):
    images = {}
    for image in os.listdir(dir):
        if image == ".DS_Store":
            continue
        images[image] = pg.image.load(os.path.join(dir,image))
    return images

class ReturnableThread(th.Thread):
    # This class is a subclass of Thread that allows the thread to return a value.
    def __init__(self, target):
        th.Thread.__init__(self)
        self.target = target
        self.result = None
    
    def run(self) -> None:
        self.result = self.target()

def generateGradient(col1, col2, w=640, h=480, a1=255, a2=255):
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

def generatebggrad():
    c1 = (16, 32, 128)
    c2 = (0, 16, 64)
    bgsurf = pg.Surface((640, 338))
    bgsurf.fill(c1)
    bgsurf.blit(generateGradient(c2, c1, w=640, h=136), (0, 0))
    bgsurf.blit(generateGradient(c1, c2, w=640, h=136), (0, 338-136))
    return bgsurf

def getxyfromlatlong(lat, long, offsetx, offsety) -> tuple[float, float]:
    #credits to ws4kp
    x = 0
    y = 0
    imgwidth = 5100
    imgheight = 3200
    y = (51.75 - float(lat))*55.2
    y -= offsety
    if y > (imgheight - offsety * 2):
        y = imgheight - offsety * 2
    elif y < 0:
        y = 0
    
    x = -41.775 * (-130.37 - float(long))
    x -= offsetx
    
    if x > (imgwidth - offsetx * 2):
        x = imgwidth - offsetx * 2
    elif x < 0:
        x = 0
    
    return (x*2, y*2)

def getxyfromlatlongdoppler(lat, long, offsetx, offsety) -> tuple[float, float]:
    #credits to ws4kp again
    x = 0
    y = 0
    imgwidth = 6000
    imgheight = 2800
    y = (51 - float(lat))*61.4481
    y -= offsety
    if y > (imgheight - offsety * 2):
        y = imgheight - offsety * 2
    elif y < 0:
        y = 0
    
    x = -42.1768 * (-129.138 - float(long))
    x -= offsetx
    
    if x > (imgwidth - offsetx * 2):
        x = imgwidth - offsetx * 2
    elif x < 0:
        x = 0
    
    return (x*2, y*2)

def piltosurf(image):
    surf = pg.image.frombytes(image.tobytes(), image.size, image.mode).convert_alpha()
    image.close()
    return surf

def removedopplenoise(image):
    lg1 = (49, 210, 22, 255)
    lg2 = (0, 142, 0, 255)
    dg1 = (20, 90, 15, 255)
    dg2 = (10, 40, 10, 255)
    yl = (196, 179, 70, 255)
    orn = (190, 71, 19, 255)
    rd = (171, 14, 14, 255)
    brn = (155, 31, 4, 255)
    now = dt.now().astimezone(tz.utc)
    print(f'https://mesonet.agron.iastate.edu/archive/data/{now.year}/{zeropad(now.month)}/{zeropad(now.day)}/GIS/uscomp/{image}')
    imgbytes = r.get(f'https://mesonet.agron.iastate.edu/archive/data/{now.year}/{zeropad(now.month)}/{zeropad(now.day)}/GIS/uscomp/{image}').content
    imagg = img.open(BytesIO(imgbytes))
    imagg2 = imagg.convert("RGBA")
    imag = imagg2.load()
    width, height = imagg.size
    didit = False
    for x in range(0, width):
        for y in range(0, height):
            R, G, B, A = imag[x, y]
            black = (R==0)and(G==0)and(B==0)
            oldlg1 = (R==0)and(G==255)and(B==0)
            oldlg2 = (R==0)and(G==200)and(B==0)
            olddg1 = (R==0)and(G==144)and(B==0)
            olddg2 = (R==255)and(G==255)and(B==0)
            oldy = (R==231)and(G==192)and(B==0)
            oldo = (R==255)and(G==144)and(B==0)
            oldr = ((R==214)and(G==0)and(B==0))or((R==255)and(G==0)and(B==0))
            oldb = ((R==192)and(G==0)and(B==0))or((R==255)and(G==0)and(B==255))
            if black:
                imag[x, y] = (0, 0, 0, 0)
                if not didit:
                    didit = True
            elif oldlg1:
                imag[x, y] = lg1
            elif oldlg2:
                imag[x, y] = lg2
            elif olddg1:
                imag[x, y] = dg1
            elif olddg2:
                imag[x, y] = dg2
            elif oldy:
                imag[x, y] = yl
            elif oldo:
                imag[x, y] = orn
            elif oldr:
                imag[x, y] = rd
            elif oldb:
                imag[x, y] = brn
    return piltosurf(imagg2)

def degrees_to_compass(degrees):
    if degrees == None:
        return "XX"
    """Converts degrees (0-360) to 16-point compass direction."""

    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

    index = round(degrees / 22.5) % 16  # Calculate index, wrap around for 360

    return directions[index]

def getWeather():
    weatheraddr = getattr(vars, "weatheraddr", "http://wttr.in?format=j2")
    global loading
    loading = True
    global loadingText
    loadingText = "Loading..."
    global stationinfo
    global ticker
    global wttr
    wttr = not forcecoords
    global weather
    ticker = "Please be patient!"
    
    
    if wttr:
        try:
            weather = r.get(weatheraddr).json()
            weatherend = r.get(f'https://api.weather.gov/points/{weather["nearest_area"][0]["latitude"]},{weather["nearest_area"][0]["longitude"]}').json()
        except:
            wttr = False
            global coords
            if getattr(vars, "coords", False) == False:
                loadingText = "Check Terminal"
                print("Error: Wttr.in is down! Please input your coordinates (lat,long).")
                coords = input("coordinates: ")
            else:
                coords = vars.coords
    else:
        if getattr(vars, "coords", False) == False:
            loadingText = "Check Terminal"
            print("Error: Wttr.in is down! Please input your coordinates (lat,long).")
            coords = input("coordinates: ")
        else:
            coords = vars.coords
    weatherend = r.get(f'https://api.weather.gov/points/{coords}').json()
    weatherendpoint1 = weatherend["properties"]["observationStations"]
    weatherendpoint2 = weatherend["properties"]["forecast"]
    weatherendpoint3 = weatherend["properties"]["forecastHourly"]
    weatherendpoint4 = weatherend["properties"]["forecastGridData"]
    if getattr(vars, "station"):
        stationname = vars.station
    else:
        stationname = r.get(weatherendpoint1).json()["features"][0]["properties"]["stationIdentifier"]
    print(stationname)
    global weather2 # current
    loadingText="Retrieving conditions..."
    weather2 = r.get(f'https://api.weather.gov/stations/{stationname}/observations').json()
    stationinfo = r.get(f'https://api.weather.gov/stations/{stationname}/').json()
    global weather3 # forecast
    loadingText="Retrieving forecast..."
    weather3 = r.get(weatherendpoint2).json()
    global weather4
    weather4 = r.get(weatherendpoint3).json()
    global weatherraw
    weatherraw = r.get(weatherendpoint4).json()
    global alerts
    if wttr:
        alerts = r.get(f'https://api.weather.gov/alerts/active?message_type=alert&point={weather["nearest_area"][0]["latitude"]},{weather["nearest_area"][0]["longitude"]}').json()["features"]
    else:
        alerts = r.get(f'https://api.weather.gov/alerts/active?message_type=alert&point={coords}').json()["features"]
    global bgassets
    global currentassets
    global regionalassets
    global extendedassets
    global moonassets
    global miscassets
    
    loadingText = "Preloading backgrounds..."
    bgassets = preload(bgassetsp)
    loadingText = "Preloading icons..."
    currentassets = preload(currentassetsp)
    regionalassets = preload(regionalassetsp)
    extendedassets = preload(extendedassetsp)
    moonassets = preload(moonassetsp)
    miscassets = preload(miscassetsp)
    #fonts
    loadingText = "Preloading fonts..."
    global smallfont
    global largefont24
    global largefont28
    global largefont32
    global starfont20
    global starfont24
    global starfont32
    global extendedfont
    global radarname
    smallfont = pg.font.Font(os.path.join(fontassetsp, "Small.ttf"), 32)
    largefont24 = pg.font.Font(os.path.join(fontassetsp, "Large.ttf"), 24)
    largefont28 = pg.font.Font(os.path.join(fontassetsp, "Large.ttf"), 28)
    largefont32 = pg.font.Font(os.path.join(fontassetsp, "Large.ttf"), 32)
    starfont20 = pg.font.Font(os.path.join(fontassetsp, "Main.ttf"), 20)
    starfont24 = pg.font.Font(os.path.join(fontassetsp, "Main.ttf"), 24)
    starfont32 = pg.font.Font(os.path.join(fontassetsp, "Main.ttf"), 32)
    extendedfont = pg.font.Font(os.path.join(fontassetsp, "Extended.ttf"), 32)
    radarname = pg.font.SysFont("Arial", 37, True)
    if playmusicv:
        loadingText = "Loading music..."
        print("music found!")
        music = pg.mixer.Sound(os.path.join(playmusic, rd.choice(os.listdir(playmusic))))
        music.play(-1)
    loading = False

pg.init()
window = pg.display.set_mode((640, 480), pg.SCALED)
pg.display.set_caption("My WeatherStar 4000")

def renderoutline(font, text, x, y, width, color=(0, 0, 0), surface=window):
    surface.blit(font.render(text, True, (0, 0, 0)), (x-width, y-width))
    surface.blit(font.render(text, True, (0, 0, 0)), (x+width, y-width))
    surface.blit(font.render(text, True, (0, 0, 0)), (x-width, y+width))
    surface.blit(font.render(text, True, (0, 0, 0)), (x+width, y+width))

def drawshadow(font, text, x, y, offset, color=(255, 255, 255), surface=window):
    surface.blit(font.render(text, True, (0, 0, 0)), (x+offset, y+offset))
    renderoutline(font, text, x, y, 1)
    surface.blit(font.render(text, True, color), (x, y))

viewinfo = {
    "localforecast": {
        "bg": "BackGround1.png",
        "title1": "Local",
        "title2": "Forecast",
        "dual": True,
        "noaa": True,
        "showtitle": True,
        "showtime": True,
        "showlml": True
    },
    "hourlygraph": {
        "bg": "BackGround1_Chart.png",
        "title1": "Hourly Graph",
        "title2": "",
        "dual": False,
        "noaa": False,
        "showtitle": True,
        "showtime": False,
        "showlml": True
    },
    "hourlyforecast": {
        "bg": "BackGround6.png",
        "title1": "Hourly Forecast",
        "title2": "",
        "dual": False,
        "noaa": False,
        "showtitle": True,
        "showtime": True,
        "showlml": True
    },
    "radar": {
        "bg": "BackGround4.png",
        "title1": "Local",
        "title2": "Forecast",
        "dual": True,
        "noaa": False,
        "showtitle": False,
        "showtime": False,
        "showlml": False
    }
}
view = "hourlygraph"

loadingbg = pg.image.load(os.path.join(bgassetsp, "BackGround9.png"))
loadingfont = pg.font.Font(os.path.join(fontassetsp, "Main.ttf"), 32)
loadingth = th.Thread(target=getWeather)
loadingth.start()

def mapnum(minv, maxv, nminv, nmaxv, val):
    firstspan = maxv-minv
    secondspan = nmaxv-nminv
    valsc = val-minv
    return nminv + ((valsc / firstspan) * secondspan)

clock = pg.time.Clock()

def getradarimages(var, *args):
    now = dt.now()
    radar_img_count = 6
    nowutc = now.astimezone(tz.utc)
    nowutc.replace(minute=(5 * (nowutc.minute // 5)))
    latest_image = nowutc.strftime("n0r_%Y%m%d%H%M.png")
    if not latest_image[-5] in ["0", "5"]:
        if int(latest_image[-5]) > 5:
            lver = list(latest_image)
            lver[-5] = "5"
            latest_image = "".join(lver)
        elif int(latest_image[-5]) > 0:
            lver = list(latest_image)
            lver[-5] = "0"
            latest_image = "".join(lver)
    
    print(latest_image)
    #try:
    #    r.get(f'https://mesonet.agron.iastate.edu/archive/data/{now.year}/{zeropad(now.month)}/{zeropad(now.day)}/GIS/uscomp/{latest_image}')
    #except:
    #    nowutc.replace(minute=(nowutc.minute - 5))
    for i in range(radar_img_count):
        pass
    removed = removedopplenoise(latest_image)
    var = [removed]
    return [removed]
    #return [removedopplenoise(latest_image)]

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
def parseRawTimeStamp(timestamp) -> tuple[dt, dt, int]:
    time = dt.strptime(timestamp, "%Y-%m-%dT%H:%M:%S+00:00/"+timestamp.split("/")[1])
    time = time - td(hours=4)
    periodtime = parsetimelength(timestamp)
    return (time, time + td(hours=periodtime), periodtime)

def getValuesHourly(values):
    #we need to get 24 hours of values
    
    #find offset
    now = dt.now()
    offset = 0
    alltimes = []
    for value in range(len(values)):
        ti = values[value]["validTime"].split("/")[0]
        length = it.parse_duration(values[value]["validTime"].split("/")[1])
        time = it.parse_datetime(ti).astimezone(tz.timezone(getattr(vars, "timezone", "EST")))
        tim = length.seconds / 3600
        tim += length.days * 24
        for i in range(int(tim)):
            alltimes.append((time + td(hours=i)).astimezone(tz.timezone(getattr(vars, "timezone", "EST"))))
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
    surf = pg.Surface((532, 285)).convert_alpha()
    
    temps = []
    cloud = getValuesHourly(weatherraw["properties"]["skyCover"]["values"])
    precip = getValuesHourly(weatherraw["properties"]["probabilityOfPrecipitation"]["values"])
    #for val in getValuesHourly(weatherraw["properties"]["temperature"]["values"]):
    #    temps.append(round(float(val)*1.8+32))
    offset = 0
    for pd in weather4["properties"]["periods"][(0+offset):(25+offset)]:
        temps.append(round(float(pd["temperature"])*1.8+32))
    mintemp = min(temps)
    maxtemp = max(temps)
    #medtemp = round((mintemp+maxtemp)/2)
    #time = dt.now(tz.utc)
    #order: cloud, precip, temp
    surf.fill((255, 255, 255, 0))
    
    for i in range(24):
        pg.draw.line(surf, (0, 0, 0), (mapnum(0, 24, 4, 530, i), mapnum(100, 0, 4, 281, cloud[i])+2), (mapnum(0, 24, 4, 530, i+1), mapnum(100, 0, 4, 281, cloud[i+1])+2), 4)
    for i in range(24):
        pg.draw.line(surf, (211, 211, 211), (mapnum(0, 24, 4, 530, i), mapnum(100, 0, 4, 281, cloud[i])), (mapnum(0, 24, 4, 530, i+1), mapnum(100, 0, 4, 281, cloud[i+1])), 2)
    for i in range(24):
        pg.draw.line(surf, (0, 0, 0), (mapnum(0, 24, 4, 530, i), mapnum(100, 0, 4, 281, precip[i])+2), (mapnum(0, 24, 4, 530, i+1), mapnum(100, 0, 4, 281, precip[i+1])+2), 4)
    for i in range(24):
        pg.draw.line(surf, (0, 255, 255), (mapnum(0, 24, 4, 530, i), mapnum(100, 0, 4, 281, precip[i])), (mapnum(0, 24, 4, 530, i+1), mapnum(100, 0, 4, 281, precip[i+1])), 2)
    for i in range(24):
        pg.draw.line(surf, (0, 0, 0), (mapnum(0, 24, 4, 530, i), mapnum(maxtemp, mintemp, 4, 281, temps[i])+2), (mapnum(0, 24, 4, 530, i+1), mapnum(maxtemp, mintemp, 4, 281, temps[i+1])+2), 4)
    for i in range(24):
        pg.draw.line(surf, (255, 0, 0), (mapnum(0, 24, 4, 530, i), mapnum(maxtemp, mintemp, 4, 281, temps[i])), (mapnum(0, 24, 4, 530, i+1), mapnum(maxtemp, mintemp, 4, 281, temps[i+1])), 2)
    return surf

def main():
    global dataloading
    dataloading = False
    working = True
    dual = True
    radarimages = []
    lmltimer = 240
    lmlindex = 0
    try:
        global ticker
        ticker = ""
    finally:
        pass
    while working:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                working = False
        if not working:
            break
        today = dt.now()
        day = today.strftime("%-d")
        if len(day) < 2:
            day = " " + day
        datestr = (" " + today.strftime("%a %b ") + day).upper()
        timestr = today.strftime("%-I:%M:%S %p").upper()
        timestrshort = today.strftime("%-I:%M %p").upper()
        if len(timestr) < 11:
            timestr = " " + timestr
        if len(timestrshort) < 8:
            timestrshort = " " + timestrshort
        if loading:
            window.blit(loadingbg, (0, 0))
            #drawshadow(loadingfont, loadingText, 170, 33, 3)
            #drawshadow(loadingfont, "Bottom Text", 170, 56, 3)
            drawshadow(loadingfont, loadingText, 170, 40, 3, color=(255, 255, 0))
        else:
            periods = weather3["properties"]["periods"]
            dual = viewinfo[view]["dual"]
            window.blit(bgassets[viewinfo[view]["bg"]], (0, 0))
            window.blit(miscassets["logo.png"], (50, 30))
            if viewinfo[view]["showtitle"]:
                if not dual:
                    drawshadow(starfont32, viewinfo[view]["title1"], 170, 40, 3, color=(255, 255, 0))
                else:
                    drawshadow(starfont32, viewinfo[view]["title1"], 170, 27, 3, color=(255, 255, 0))
                    drawshadow(starfont32, viewinfo[view]["title2"], 170, 56, 3, color=(255, 255, 0))
            if viewinfo[view]["noaa"]:
                window.blit(miscassets["noaa.gif"], (356, 39))
            
            if view == "localforecast":
                drawshadow(starfont32, "\n".join(wraptext(f'{periods[0]["name"]}...{periods[0]["detailedForecast"]}'.upper(), pg.Rect(74, 105, 492, 280), starfont32)), 74, 105, 3)
            elif view == "hourlygraph":
                temps = []
                for period in weather4["properties"]["periods"][:24]:
                    temps.append(round(period["temperature"]))
                mintemp = min(temps)
                maxtemp = max(temps)
                medtemp = round((mintemp+maxtemp)/2)
                now = dt.now()
                now6 = dt.now() + td(hours=6)
                now12 = dt.now() + td(hours=12)
                now18= dt.now() + td(hours=18)
                now24 = dt.now() + td(hours=24)
                time1 = now.strftime("%-I") + ("A" if (now.strftime("%p") == "AM") else "P")
                time2 = now6.strftime("%-I") + ("A" if (now6.strftime("%p") == "AM") else "P")
                time3 = now12.strftime("%-I") + ("A" if (now12.strftime("%p") == "AM") else "P")
                time4 = now18.strftime("%-I") + ("A" if (now18.strftime("%p") == "AM") else "P")
                time5 = now24.strftime("%-I") + ("A" if (now24.strftime("%p") == "AM") else "P")
                drawshadow(smallfont, "TEMPERATURE", 640-60-smallfont.size("TEMPERATURE")[0], 17, 3, (255, 0, 0))
                drawshadow(smallfont, "CLOUD %", 640-60-smallfont.size("CLOUD %")[0], 17+18, 3, (211, 211, 211))
                drawshadow(smallfont, "PRECIP %", 640-60-smallfont.size("PRECIP %")[0], 17+36, 3, (0, 255, 255))
                drawshadow(smallfont, time1, 25, 365, 3, (255, 255, 0))
                drawshadow(smallfont, time2, 158, 365, 3, (255, 255, 0))
                drawshadow(smallfont, time3, 291, 365, 3, (255, 255, 0))
                drawshadow(smallfont, time4, 424, 365, 3, (255, 255, 0))
                drawshadow(smallfont, time5, 557, 365, 3, (255, 255, 0))
                drawshadow(smallfont, str(maxtemp)+"°", 4, 75, 3, (255, 255, 0))
                drawshadow(smallfont, str(medtemp)+"°", 4, 215, 3, (255, 255, 0))
                drawshadow(smallfont, str(mintemp)+"°", 4, 338, 3, (255, 255, 0))
                window.blit(makehourlygraph(), (50, 90))
            elif view == "hourlyforecast":
                pass
            elif view == "radar":
                drawshadow(radarname, "Local", 152, 26, 3)
                drawshadow(radarname, "Radar", 152, 61, 3)
                drawshadow(starfont24, "Light", 315, 60, 3)
                drawshadow(starfont24, "Heavy",  550, 60, 3)
                #pg.draw.rect(window, (0, 0, 0), pg.Rect(640-180-154/2, 58, 154, 28), width=2)
                pg.draw.rect(window, (0, 0, 0), pg.Rect(383, 58, 154, 30), width=0)
                pg.draw.rect(window, (49, 210, 22), pg.Rect(385, 60, 17, 26), width=0)
                pg.draw.rect(window, (28, 138, 18), pg.Rect(385+19, 60, 17, 26), width=0)
                pg.draw.rect(window, (20, 90, 15), pg.Rect(385+19*2, 60, 17, 26), width=0)
                pg.draw.rect(window, (10, 40, 10), pg.Rect(385+19*3, 60, 17, 26), width=0)
                pg.draw.rect(window, (196, 179, 70), pg.Rect(385+19*4, 60, 17, 26), width=0)
                pg.draw.rect(window, (190, 72, 19), pg.Rect(385+19*5, 60, 17, 26), width=0)
                pg.draw.rect(window, (171, 14, 14), pg.Rect(385+19*6, 60, 17, 26), width=0)
                pg.draw.rect(window, (171, 14, 14), pg.Rect(385+19*7, 60, 17, 26), width=0)
                drawshadow(starfont24, "PRECIP", 480-starfont24.size("PRECIP")[0]/2-20, 32, 3, color=(255, 255, 255))
                drawshadow(smallfont, timestrshort, 480-smallfont.size(timestrshort)[0]/2-20, 80, 3, color=(255, 255, 255))
                if radarimages == [] and not dataloading:
                    dataloading = True
                    radarth = ReturnableThread(lambda: getradarimages(dataloading))
                    radarth.start()
                if radarth.result != None:
                    radarimages = radarth.result
                
                if wttr:
                    lat = weather["nearest_area"][0]["latitude"]
                    long = weather["nearest_area"][0]["longitude"]
                else:
                    lat, long = coords.split(",")
                
                offsetx = 120
                offsety = 69
                offsetx *= 2
                offsety *= 2
                sourcex, sourcey = getxyfromlatlong(lat, long, offsetx, offsety)
                
                radaroffsetx = 120
                radaroffsety = 70
                radaroffsetx *= 2
                radaroffsety *= 2
                sourcerx, sourcery = getxyfromlatlongdoppler(lat, long, offsetx, offsety)
                sourcerx /= 2
                sourcery /= 2
                #window.blit(bgassets["4000RadarMap.jpg"], (sourcex, sourcey), pg.Rect(sourcex, sourcey, 640, 367))
                buffer = pg.Surface((offsetx*2, offsety*2))
                buffer.blit(bgassets["4000RadarMap.jpg"], (0, 0), pg.Rect(sourcex, sourcey, offsetx*2, offsety*2))
                window.blit(pg.transform.smoothscale(buffer, (640, 367)), (0, 480-367))
                if radarimages != []:
                    dataloading = False
                    #buffer = pg.Surface((radaroffsetx*2, round(radaroffsety*2.33)))
                    #window.blit(radarimages[0], (0, 0), pg.Rect(sourcerx, sourcery, radaroffsetx*2, round(radaroffsety*2.33)))
                    #window.blit(pg.transform.scale(buffer, (640, 367)), (0, 480-367))
                    drawshadow(largefont32, "No Data", 320-largefont32.size("No Data")[0]/2, 240-largefont32.size("No Data")[1]/2, 3)
            
            if dataloading:
                drawshadow(largefont32, "Loading...", 320-largefont32.size("Loading...")[0]/2, 240-largefont32.size("Loading...")[1]/2, 3)
            
            if viewinfo[view]["showtime"] or loading:
                drawshadow(smallfont, timestr, 415, 30, 3, color=(255, 255, 255))
                drawshadow(smallfont, datestr, 415, 52, 3, color=(255, 255, 255))
        if loading:
            drawshadow(loadingfont, "Please be patient!", 55, 410, 3)
        if viewinfo[view]["showlml"] and not loading:
            drawshadow(starfont32, ticker, 55, 410, 3)
        if not loading:
            if lmltimer > 0:
                lmltimer -= 1
            else:
                lmltimer = 240
                lmlindex += 1
                if lmlindex == 6:
                    lmlindex = 0
            if lmlindex == 0:
                ticker = f'Conditions at {stationinfo["properties"]["name"][:20]}'
            elif lmlindex == 1:
                ticker = f'Temp: {round(weather2["features"][0]["properties"]["temperature"]["value"]*1.8+32)}°F'
                if weather2["features"][0]["properties"]["heatIndex"]["value"]:
                    ticker += f' Heat Index: {round(weather2["features"][0]["properties"]["heatIndex"]["value"]*1.8+32)}°F'
                elif weather2["features"][0]["properties"]["windChill"]["value"]:
                    ticker += f' Wind Chill: {round(weather2["features"][0]["properties"]["windChill"]["value"]*1.8+32)}°F'
            elif lmlindex == 2:
                ticker = f'Humidity: {round(weather2["features"][0]["properties"]["relativeHumidity"]["value"])}% Dewpoint: {round(weather2["features"][0]["properties"]["dewpoint"]["value"]*1.8+32)}°F'
            elif lmlindex == 3:
                ticker = f'Barometric Pressure: {round(weather2["features"][0]["properties"]["barometricPressure"]["value"]/3386, 2)}'
            elif lmlindex == 4:
                if weather2["features"][0]["properties"]["windDirection"]["value"]:
                    ticker = f'Wind: {degrees_to_compass(weather2["features"][0]["properties"]["windDirection"]["value"])} {weather2["features"][0]["properties"]["windSpeed"]["value"]}'
                else:
                    if weather2["features"][0]["properties"]["windSpeed"]["value"] > 0:
                        ticker = f'Wind: {round(weather2["features"][0]["properties"]["windSpeed"]["value"]/1.609)} MPH'
                    else:
                        ticker = "Wind: Calm"
            elif lmlindex == 5:
                ceiling = weather2["features"][0]["properties"]["cloudLayers"][0]["base"]["value"]*3.281
                ticker = f'Visib: {round(weather2["features"][0]["properties"]["visibility"]["value"]/1609)} mi. Ceiling: {"Unlimited" if ceiling == 0 else round(ceiling/100)*100} ft.'
        pg.display.flip()
        clock.tick(60)
main()