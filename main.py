import threading as th
import requests as r
import pygame as pg
import datetime as dt
from io import BytesIO
import vars

#note: your vars file must have the following variables:
# daytheme (str) (local path to any pygame-playable format. three are included by default)
# nighttheme (str) (theme if it's past sunset or before sunrise. three are included by default)
#these are optional:
# weatheraddr (str) (http://wttr.in?format=j2 by default)
# no more right now

#the todo list
#TODO: add images and national weather service descriptions. make it optional
#TODO: add a way to organize views
#TODO: add the hourly forecast
#TODO: hurricane images
#TODO: make the mouse work better
#TODO: icons to show if the mouse does something
#TODO: add a new executable that replicates a certain 90s weather thing

timeformat = "%I:%M %p"

weatheraddr = getattr(vars, "weatheraddr", "http://wttr.in?format=j2")

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
window = pg.display.set_mode((1024, 768))
pg.display.set_caption("My Weather Station")

daytheme = pg.mixer.Sound(vars.daytheme)
nighttheme = pg.mixer.Sound(vars.nighttheme)

def generateGradient(col1, col2, w=1024, h=768, a1=255, a2=255):
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

def generateGradientHoriz(col1, col2, w=1024, h=768, a1=255, a2=255):
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
    wttr = True
    loadingstage=0
    loadingtext="Loading..."
    try:
        weather = r.get(weatheraddr).json()
        weatherend = r.get(f'https://api.weather.gov/points/{weather["nearest_area"][0]["latitude"]},{weather["nearest_area"][0]["longitude"]}').json()
    except:
        wttr = False
        print("Error: Wttr.in is down! Please input your coordinates (lat,long).")
        coords = input("coordinates: ")
        weatherend = r.get(f'https://api.weather.gov/points/{coords}').json()
    loadingstage=1
    loadingtext="Retrieving stations..."
    weatherendpoint1 = weatherend["properties"]["observationStations"]
    weatherendpoint2 = weatherend["properties"]["forecast"]
    stationname = r.get(weatherendpoint1).json()["features"][0]["properties"]["stationIdentifier"]
    print(stationname)
    global weather2 # current
    loadingstage=2
    loadingtext="Retrieving current\nconditions..."
    weather2 = r.get(f'https://api.weather.gov/stations/{stationname}/observations').json()
    global weather3 # forecast
    loadingtext="Retrieving forecast..."
    loadingstage=3
    weather3 = r.get(weatherendpoint2).json()
    global alerts
    if wttr:
        alerts = r.get(f'https://api.weather.gov/alerts/active?message_type=alert&point={weather["nearest_area"][0]["latitude"]},{weather["nearest_area"][0]["longitude"]}').json()["features"]
    else:
        alerts = r.get(f'https://api.weather.gov/alerts/active?message_type=alert&point={coords}').json()["features"]
    global weathericons
    global weathericonbig
    loadingtext="Loading icons..."
    weathericons = [None for _ in range(14)]
    loadingstage=4
    for i in range(14):
        weathericons[i] = pg.image.load(BytesIO(r.get(weather3["properties"]["periods"][i]["icon"]+"&size=128").content))
    weathericonbig = pg.image.load(BytesIO(r.get(weather2["features"][0]["properties"]["icon"]+"&size=192").content))
    global loading
    loading = False

gradient = generateGradient((0, 80, 255), (0, 180,  255))
topgradient = generateGradientHoriz((34, 139, 34), (124, 252, 0), h=64)
bottomgradient = generateGradientHoriz((240, 128, 128), (178, 34, 34), h=64)
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

fontname = "Arial"
bold = True
sizemult = 1
smallfont = pg.font.SysFont(fontname, round(24 * sizemult), bold=bold)
smallishfont = pg.font.SysFont(fontname, round(33 * sizemult), bold=bold)
smallmedfont = pg.font.SysFont(fontname, round(42 * sizemult), bold=bold)
medfont = pg.font.SysFont(fontname, round(60 * sizemult), bold=bold)
bigfont = pg.font.SysFont(fontname, round(96 * sizemult), bold=bold)
hugefont = pg.font.SysFont(fontname, round(144 * sizemult), bold=bold)
giganticfont = pg.font.SysFont(fontname, round(320 * sizemult), bold=bold)

weatherth = th.Thread(target=getWeather)
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

def drawshadowtext(text, size, x, y, offset, shadow=127):
    text = str(text)
    textn = size.render(text, 1, (255, 255, 255, 0))
    textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
    textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return size.render(text, 1, (255, 255, 255, 255))

def drawshadowtemp(temp, size: pg.font.Font, x, y, offset, shadow=127):
    temp = str(temp)
    textn = size.render(temp, 1, (255, 255, 255, 255))
    textsh = size.render(temp, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
    if len(temp) == 3:
        textn = pg.transform.smoothscale_by(textn, (2/3, 1))
        textsh = pg.transform.smoothscale_by(textsh, (2/3, 1))
    textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
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

def drawshadowtextcol(text, col, size, x, y, offset, shadow=127):
    text = str(text)
    textn = size.render(text, 1, col)
    textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
    textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
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

def drawshadowbigcrunch(text, col, size, x, y, offset, targetWidth, targetHeight, shadow=127):
    text = str(text)
    textn = size.render(text, 1, col)
    textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
    if textn.get_width() > targetWidth:
        textn = pg.transform.smoothscale_by(textn, (targetWidth/textn.get_width(), 1))
        textsh = pg.transform.smoothscale_by(textsh, (targetWidth/textsh.get_width(), 1))
    if textn.get_height() > targetHeight:
        textn = pg.transform.smoothscale_by(textn, (1, targetHeight/textn.get_height()))
        textsh = pg.transform.smoothscale_by(textsh, (1, targetHeight/textsh.get_height()))
    textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return size.render(text, 1, (255, 255, 255, 255))

def drawshadowtempcol(temp, col, size: pg.font.Font, x, y, offset, shadow=127):
    temp = str(temp)
    textn = size.render(temp, 1, col)
    textsh = size.render(temp, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
    if len(temp) == 3:
        textn = pg.transform.smoothscale_by(textn, (2/3, 1))
        textsh = pg.transform.smoothscale_by(textsh, (2/3, 1))
    textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return textn

def formatMetric(metric):
    if metric["value"] == None:
        return "Error"
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

pg.event.pump()
def main():
    bottomtomorrow = False
    working = True
    playingmusic = 0
    view = 0
    alertscroll = 0
    alertshow = 0
    showingalert = 0
    alerttimer = 300
    clock = pg.time.Clock()
    night = False
    nightv= False
    try:
        global loading
        loading = True
    except:
        pass
    while working:
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
                        if view > 3:
                            view = 0
        if not working:
            break
        window.blit(gradient, (0, 0))
        if loading:
            loadtext = bigfont.render(loadingtext, 1, (255, 255, 255, 255))
            loadshadow = bigfont.render(loadingtext, 1, (0, 0, 0, 100))
            alphablit(loadshadow, 127, (512-loadtext.get_width()/2+10, 384-loadtext.get_height()/2+10))
            window.blit(loadtext, (512-loadtext.get_width()/2, 384-loadtext.get_height()/2))
        else:
            if True:
                now = dt.datetime.now()
                if wttr:
                    sunset = dt.datetime.strptime(weather["weather"][0]["astronomy"][0]["sunset"], timeformat)
                    sunrise = dt.datetime.strptime(weather["weather"][0]["astronomy"][0]["sunrise"], timeformat)
                obstime = dt.datetime.strptime(weather2["features"][0]["properties"]["timestamp"] + "UTC", "%Y-%m-%dT%H:%M:%S+00:00%Z")
                obstimeshort = obstime.strftime("%-I:%M %p")
                night = False
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
                if wttr:
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
            window.blit(topshadow, (0, 64), special_flags=pg.BLEND_RGBA_MULT)
            window.blit(topgradient, (0, 0))
            
            if view == 0:
                window.blit(topshadow, (0, 524), special_flags=pg.BLEND_RGBA_MULT)
                window.blit(topgradient, (0, 460))
                drawshadowtext(periods[bottomtomorrow]["name"].upper(), smallmedfont, 5, 465, 5, 127)
            
            viewnames = ["Split View", "Overview", "7-Day Forecast", "Alerts"]
            viewName = viewnames[view]
            if view == 2:
                viewName = ["7-Day Forecast (Day)", "7-Day Forecast (Night)", "7-Day Forecast (Page 1)", "7-Day Forecast (Page 2)", "7-Day Forecast (Compact)"][nightv]
            if wttr:
                location = smallmedfont.render(weather["nearest_area"][0]["areaName"][0]["value"], 1, (255, 255, 255, 255))
            drawshadowtext(viewName, smallmedfont, 512-smallmedfont.size(viewName)[0]/2, 5, 5, 127)
            drawshadowtext("CURRENT", smallmedfont, 5, 5, 5, 127)
            if wttr:
                drawshadowtext(weather["nearest_area"][0]["areaName"][0]["value"], smallmedfont, 1024-10-location.get_width(), 5, 5, 127)
            #today
            # today's forecast (min, axg, max) (deprecated)
            #drawshadowtemp("Previous 24h extremes:", smallmedfont, 5, 80, 5, 127)
            #drawshadowtempcol(round(formatMetric(weather2["features"][0]["properties"]["minTemperatureLast24Hours"])), (135, 206, 250, 255), smallmedfont,405, 80, 5, 127)
            #drawshadowtempcol(round(formatMetric(weather2["features"][0]["properties"]["maxTemperatureLast24Hours"])), (255, 140, 0, 255), smallmedfont, 480, 80, 5, 127)
            # alerts
            if view != 3:
                if len(alerts) > 0:
                    if len(alerts) > 1:
                        if alerttimer > 0:
                            alerttimer -= 1
                        else:
                            alertscroll += 5
                    if alertscroll > 1024:
                        showingalert += 1
                        alertscroll = 0
                        alerttimer = 300
                        if showingalert > len(alerts)-1:
                            showingalert = 0
                    drawshadowcrunchcol(alerts[showingalert]["properties"]["headline"], (255, 0, 0), smallmedfont, 5 + alertscroll, 80, 5, 1024-15, 127)
                    if len(alerts) > 1:
                        drawshadowcrunchcol(alerts[(showingalert+1) if showingalert != len(alerts)-1 else 0]["properties"]["headline"], (255, 0, 0), smallmedfont, -1019 + alertscroll, 80, 5, 1024-15, 127)
                else:
                    drawshadowtext("No active alerts in your area.", smallmedfont, 5, 80, 5, 127)
            # current
            if view in [0, 1]:
                precip = weather2["features"][0]["properties"]["precipitationLastHour"]["value"]
                if precip == None:
                    precip = "Error"
                else:
                    precip = str(round(precip/25.4, 1))
                currenttemp = drawshadowtemp(round(formatMetric(weather2["features"][0]["properties"]["temperature"])), giganticfont, 60, 80, 20, 180)
                drawshadowtext("°F", bigfont, currenttemp.get_width()+60, 125, 10, 160)
                drawshadowtext(f'Wind: {degrees_to_compass(weather2["features"][0]["properties"]["windDirection"]["value"])} @ {round(formatMetric(weather2["features"][0]["properties"]["windSpeed"]))}mph', smallmedfont, 540, 125, 5, 127)
                drawshadowtext(f'Rel. Humidity: {roundd(weather2["features"][0]["properties"]["relativeHumidity"]["value"], 1)}%', smallmedfont, 540, 175, 5, 127)
                drawshadowtext(f'Precipitation: {precip} in.', smallmedfont, 540, 225, 5, 127)
                drawshadowtext(f'Visibility: {round(weather2["features"][0]["properties"]["visibility"]["value"]/1609, 1)} mi.', smallmedfont, 540, 275, 5, 127)
                drawshadowtext(f'Heat Index: {round(formatMetric(fallback(weather2["features"][0]["properties"]["heatIndex"], weather2["features"][0]["properties"]["temperature"])))}°F', smallmedfont, 540, 325, 5, 127)
                drawshadowtext(f'Air pressure: {roundd(formatMetric(weather2["features"][0]["properties"]["barometricPressure"]), 2)} inHg', smallmedfont, 540, 375, 5, 127)
                #window.blit(currenttemp, (60, 80))
                drawshadowtext(weather2["features"][0]["properties"]["textDescription"], smallmedfont, 60+currenttemp.get_width()/2-currentcondition.get_width()/2, 400, 5, 127)
                
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
                    drawshadowcrunch(periods[bottomtomorrow]["shortForecast"], smallmedfont, 440, 640, 5, 1024-440-10, 127)
                else:
                    drawshadowtext("\n".join(wraptext(periods[0]["detailedForecast"], pg.Rect(350, 480, 1024-350-15, 768-64-15), smallfont)), smallfont, 350, 480, 5, 127)
                    buffer = pg.Surface((192, 192))
                    pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 192, 192))
                    buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                    window.blit(buffer, (110, 490), special_flags=pg.BLEND_RGBA_MULT)
                    window.blit(weathericonbig, (100, 480))
            elif view == 2:
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
                    for j in range(14):
                        i = j%7
                        drawingn = (j > 6)
                        buffer = pg.Surface((140, 276))
                        pg.draw.rect(buffer, (127, 127, 127, 127), pg.rect.Rect(0, 0, 140, 276))
                        buffer = pg.transform.gaussian_blur(expandSurface(buffer, 6), 4)
                        window.blit(buffer, (20 + i*142, 133+280*drawingn), special_flags=pg.BLEND_RGBA_MULT)
                        window.blit(weekbgc if not drawingn else weekbgnc, (15 + i*142, 128+280*drawingn))
                        if nowisday and i == 0:
                            continue
                        if not nowisday and i == 6 and drawingn:
                            continue
                        drawshadowtext(periods[i*2+(not nowisday)+drawingn]["name"][0:3].upper(), smallmedfont, 15+i*142+70-smallmedfont.size(periods[i*2+(not nowisday)+drawingn]["name"][0:3].upper())[0]/2, 138+280*drawingn, 5, 127)
                        drawshadowtemp(periods[i*2+(not nowisday)+drawingn]["temperature"], medfont, 52 + i*142, 172+280*drawingn, 5, 127)
                        window.blit(weathericons[i*2+(not nowisday)+drawingn], (21+142*i, 417+128+5-280*(not drawingn)))
                        drawshadowtext(f'Wind: {periods[i+(drawingn-2)*7]["windDirection"]}', smallfont, 84+i*142-smallfont.size(f'Wind: {periods[i+(drawingn-2)*7]["windDirection"]}')[0]/2, 234+280*drawingn, 5, 127)
            elif view == 3:
                if len(alerts) > 0:
                    drawshadowbigcrunch(alerts[alertshow]["properties"]["description"], (255, 224, 224), smallmedfont, 15, 96, 5, 994, 588, 127)
                else:
                    drawshadowtext("No active alerts.", smallmedfont, 15, 96, 5, 127)
            #housekeeping
            window.blit(bottomgradient, (0, 704))
            drawshadowtext(f"Last updated at {obstimeshort} UTC", smallmedfont, 5, 768-64+5, 5, 127)
            window.blit(bottomshadow, (0, 768-64-16), special_flags=pg.BLEND_RGBA_MULT)
        pg.display.flip()
        clock.tick(60)
main()