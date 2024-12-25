import pygame as pg
pg.init()
import requests as r
import map_tile_stitcher as ms
import datetime as dt
import os
import sys
import argparse as ap
import vars as varr
import geocoder as gc
from datetime import datetime as dt

screenwidth = 1366
screendiff = screenwidth - 1024

apikey = varr.apikey
unites = getattr(varr, "units", "e")

uvcolors = [
    (151, 215, 0),
    (151, 215, 0),
    (151, 215, 0),
    (252, 227, 0),
    (252, 227, 0),
    (252, 227, 0),
    (255, 130, 0),
    (255, 130, 0),
    (239, 51, 64),
    (239, 51, 64),
    (239, 51, 64),
    (144, 99, 205)
]

rheaders = {
    "User-Agent": "(lewolfyt.github.io, localscope+ciblox3@gmail.com)"
}

if True:
    if True:
        if getattr(varr, "coords", False):
            coords = getattr(varr, "coords")
        else:
            templl = gc.ip("me")
            gj = templl.geojson
            coords = f'{gj["features"][0]["lat"]},{gj["features"][0]["lng"]}'
        weatherend = r.get(f'https://api.weather.gov/points/{coords}', headers=rheaders).json()

parser = ap.ArgumentParser(
    prog="static.py",
    description="Generates static weather displays for use in multimedia settings."
)

gens = ["current"]

parser.add_argument("generator")
parser.add_argument("-o", "--output")
#parser.add_argument()

args = parser.parse_args(sys.argv[1:])

fpath = args.output
if fpath == None:
    fpath = "output.png"
gen = args.generator

window = pg.Surface((screenwidth, 768))

global weather_elements #keeps all weather data generated
weather_elements = {}

fontname = getattr(varr, "font", "Arial")
bold = getattr(varr, "bold", True)
sizemult = 1
if getattr(varr, "sysfont", True):
    tinyfont = pg.font.SysFont(fontname, round(18 * sizemult), bold=bold)
    smallfont = pg.font.SysFont(fontname, round(24 * sizemult), bold=bold)
    smallishfont = pg.font.SysFont(fontname, round(33 * sizemult), bold=bold)
    smallmedfont = pg.font.SysFont(fontname, round(42 * sizemult), bold=bold)
    medfont = pg.font.SysFont(fontname, round(60 * sizemult), bold=bold)
    bigfont = pg.font.SysFont(fontname, round(96 * sizemult), bold=bold)
    #hugefont = pg.font.SysFont(fontname, round(144 * sizemult), bold=bold)
    giganticfont = pg.font.SysFont(fontname, round(320 * sizemult), bold=bold)
else:
    tinyfont = pg.font.Font(fontname, round(18 * sizemult))
    smallfont = pg.font.Font(fontname, round(24 * sizemult))
    smallishfont = pg.font.Font(fontname, round(33 * sizemult))
    smallmedfont = pg.font.Font(fontname, round(42 * sizemult))
    medfont = pg.font.Font(fontname, round(60 * sizemult))
    bigfont = pg.font.Font(fontname, round(96 * sizemult))
    #hugefont = pg.font.Font(fontname, round(144 * sizemult))
    giganticfont = pg.font.Font(fontname, round(320 * sizemult))

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

def roundd(val, precision=0):
    if val in [None, "Error"]:
        return "Error"
    else:
        return round(val, precision)

def generateGradient(col1, col2, w=screenwidth, h=768, a1=255, a2=255):
    r1, g1, b1 = col1[0], col1[1], col1[2]
    r2, g2, b2 = col2[0], col2[1], col2[2]
    surface = pg.Surface((w, h))
    surface.fill((255, 255, 255, 255))
    for i in range(h):
        tr = i/(h-1)
        transpar = pg.Surface((w, 1))
        transpar.fill((255, 255, 255, (a1*(1-tr) + a2*tr)))
        pg.draw.line(transpar, ((r1*(1-tr) + r2*tr), (g1*(1-tr) + g2*tr), (b1*(1-tr) + b2*tr)), (0, 0), (w, 0))
        surface.blit(transpar, (0, i), special_flags=pg.BLEND_RGBA_MULT)
    return surface

def generateGradientHoriz(col1, col2, w=screenwidth, h=768, a1=255, a2=255):
    r1, g1, b1 = col1[0], col1[1], col1[2]
    r2, g2, b2 = col2[0], col2[1], col2[2]
    surface = pg.Surface((w, h))
    surface.fill((0, 0, 0, 0))
    for i in range(w):
        tr = i/(w-1)
        pg.draw.line(surface, ((r1*(1-tr) + r2*tr), (g1*(1-tr) + g2*tr), (b1*(1-tr) + b2*tr), (a1*(1-tr) + a2*tr)), (i, 0), (i, h))
    return surface

#pg.display.set_mode()
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

def drawshadowtext(text, size, x, y, offset, shadow=127, totala=255):
    text = str(text)
    
    if True:
        textn = size.render(text, 1, (255, 255, 255, 0))
        textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
        textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
        
        if totala != 255:
            buf = pg.Surface((textsh.get_width(), textsh.get_height()))
            buf.fill((255, 255, 255))
            alphablit2(buf, 255-totala, (0, 0), textsh)
        
        textbland = size.render(text, 1, (255, 255, 255, 255))
    
    if totala != 255:
        window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
        alphablit(textn, totala, (x, y))
    else:
        window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
        window.blit(textn, (x, y))
    return textbland

def drawshadowcrunch(text, size: pg.font.Font, x, y, offset, targetWidth, shadow=127):
    textn = size.render(text, 1, (255, 255, 255, 255))
    textsh = size.render(text, 1, (shadow/1.5, shadow/1.5, shadow/1.5, shadow))
    if size.size(str(text))[0] > targetWidth:
        textn = pg.transform.smoothscale(textn, (targetWidth, size.size(text)[1]))
        textsh = pg.transform.smoothscale(textsh, (targetWidth, size.size(text)[1]))
    textsh = pg.transform.gaussian_blur(expandSurface(textsh, 6), 4)
    window.blit(textsh, (x+offset, y+offset), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(textn, (x, y))
    return textn

#these next functions are pretty self-explanatory
def get_current():
    global weather_elements
    observationend = f"https://api.weather.com/v3/wx/observations/current?geocode={coords}&units={unites}&language=en-US&format=json&apiKey={apikey}"
    weather_elements["current"] = r.get(observationend).json()

def get_extended():
    global weather_elements
    days = "7"
    extendedend = f"https://api.weather.com/v3/wx/forecast/daily/7day?geocode={coords}&format=json&units=e&language=en-US&apiKey={apikey}"
    weather_elements["extended"] = r.get(extendedend).json()

def get_hourly():
    global weather_elements

def get_health():
    global weather_elements
    healthend = f"https://api.weather.com/v3/wx/globalAirQuality?geocode={coords}&language=en-US&scale=EPA&format=json&apiKey={apikey}"
    weather_elements["health"] = r.get(healthend).json()["globalairquality"]

#these functions draw the different slides
def draw_current():
    global weather_elements
    get_current()
    get_health()
    precip = weather_elements["current"]["precip1Hour"]
    if precip == None:
        precip = "0"
    else:
        precip = str(round(precip/25.4, 1))
    window.blit(topgradient, (0, 0))
    window.blit(topshadow, (0, 64), special_flags=pg.BLEND_RGBA_MULT)
    drawshadowtext("Current Conditions", smallmedfont, 5, 5, 5)
    window.blit(bottomgradient, (0, 704))
    window.blit(bottomshadow, (0, 704-16), special_flags=pg.BLEND_RGBA_MULT)
    drawshadowtext(f"24 Hour Extremes: {weather_elements['current']['temperatureMin24Hour']} (Min) / {weather_elements['current']['temperatureMax24Hour']} (Max)", smallmedfont, 5, 69, 5)
    bland = drawshadowtext(f'{weather_elements["current"]["temperature"]}', giganticfont, 60, 80, 20, 180)
    drawshadowtext("°F", bigfont, bland.get_width()+60, 125, 10, 160)
    
    if weather_elements["current"]["windDirectionCardinal"] != "CALM":
        #print(weather_elements["current"]["features"][0]["properties"]["windSpeed"])
        drawshadowtext(f'Wind: {weather_elements["current"]["windDirectionCardinal"]} @ {round((weather_elements["current"]["windSpeed"]))} MPH', smallmedfont, 540, 125, 5, 127)
    else:
        drawshadowtext('Wind: Calm', smallmedfont, 540, 125, 5, 127)
    drawshadowtext(f'Relative Humidity: {roundd(weather_elements["current"]["relativeHumidity"], 1)}%', smallmedfont, 540, 175, 5, 127)
    drawshadowtext(f'Precipitation: {precip} inches', smallmedfont, 540, 225, 5, 127)
    drawshadowtext(f'Visibility: {round(weather_elements["current"]["visibility"], 1)} miles', smallmedfont, 540, 275, 5, 127)
    drawshadowtext(f'Feels Like: {round(weather_elements["current"]["temperatureFeelsLike"])}°F', smallmedfont, 540, 325, 5, 127)
    
    pressa = ["(-)", "(+)", "(-)", "(++)", "(--)"]
    
    drawshadowtext(f'Air pressure: {roundd(weather_elements["current"]["pressureAltimeter"], 2)} inHg {pressa[weather_elements["current"]["pressureTendencyCode"]]}', smallmedfont, 540, 375, 5, 127)
    #window.blit(currenttemp, (60, 80))
    currentcondition = smallmedfont.render(weather_elements["current"]["wxPhraseLong"], 1, (255, 255, 255, 255))
    offsetw = -currentcondition.get_width()/2
    if offsetw < -220:
        offsetw = -220
    drawshadowcrunch(weather_elements["current"]["wxPhraseLong"], smallmedfont, 60+bland.get_width()/2+offsetw, 400, 5, 440, 127)
    #air quality
    primary_pollutant = weather_elements["health"]["primaryPollutant"]
    aqi = weather_elements["health"]["airQualityIndex"]
    aqi_category = weather_elements["health"]["airQualityCategory"]
    
    window.blit(topgradient, (0, 460))
    window.blit(topshadow, (0, 524), special_flags=pg.BLEND_RGBA_MULT)
    drawshadowtext("Air Quality Information", smallmedfont, 5, 465, 5)
    drawshadowtext(f"Air Quality: {aqi} ({aqi_category})", smallmedfont, 5, 529, 5)
    drawshadowtext(f"Primary Pollutant: {primary_pollutant}", smallmedfont, 5, 574, 5)
    drawshadowcrunch(weather_elements["health"]["messages"]["General"]["text"], smallmedfont, 5, 619, 5, screenwidth-10)
    drawshadowtext(weather_elements["health"]["source"], tinyfont, 5, 664, 5)

def draw_localfcst():
    global weather_elements
    get_extended()
    pg.draw.line(window, (0, 0, 0, 127), (screenwidth/2+2, 0), (screenwidth/2+2, 768), 4)
    pg.draw.line(window, (0, 0, 0, 127), (0, 768/2+2), (screenwidth, 768/2+2), 4)
    pg.draw.line(window, (255, 255, 255), (screenwidth/2, 0), (screenwidth/2, 768), 4)
    pg.draw.line(window, (255, 255, 255), (0, 768/2), (screenwidth, 768/2), 4)
    window.blit(topgradient, (0, 0))
    window.blit(topshadow, (0, 64), special_flags=pg.BLEND_RGBA_MULT)
    drawshadowtext("Local Forecast", smallmedfont, 5, 5, 5)
    window.blit(bottomgradient, (0, 704))
    window.blit(bottomshadow, (0, 704-16), special_flags=pg.BLEND_RGBA_MULT)
    dayp = weather_elements["extended"]["daypart"][0]
    offs = (dayp["daypartName"][0] == None)
    
    drawshadowtext(f'{dayp["temperature"][offs]}°F', bigfont, 5, 69, 8)
    drawshadowtext(f'{dayp["temperature"][offs+1]}°F', bigfont, 5+screenwidth/2, 69, 8)
    drawshadowtext(f'{dayp["temperature"][offs+2]}°F', bigfont, 5, 69+768/2-64, 8)
    drawshadowtext(f'{dayp["temperature"][offs+3]}°F', bigfont, 5+screenwidth/2, 69+768/2-64, 8)
    drawshadowtext(dayp["daypartName"][offs], medfont, 5, 768/2-84, 7, 150)
    drawshadowtext(dayp["daypartName"][offs+1], medfont, 5+screenwidth/2, 768/2-84, 7, 150)
    drawshadowtext(dayp["daypartName"][offs+2], medfont, 5, 768-84-64, 7, 150)
    drawshadowtext(dayp["daypartName"][offs+3], medfont, 5+screenwidth/2, 768-84-64, 7, 150)
    

usebg = getattr(varr, "background_image_use", False)

bgimage = None
bgimager = None
if usebg:
    bgimage = pg.image.load(varr.background)
    bgimager = pg.image.load(getattr(varr, "backgroundred", varr.background))

if usebg:
    window.blit(pg.transform.smoothscale(bgimage, (screenwidth, 768)), (0, 0))
else:
    window.blit(gradient, (0, 0))

if gen == "current":
    draw_current()

if gen == "localfcst":
    draw_localfcst()

tm = dt.now().strftime('%c')
drawshadowtext(f"Generated on {tm}", smallmedfont, 5, 709, 5)

pg.image.save(window, os.path.abspath(fpath))