import threading as th
import requests as r
import pygame as pg
import datetime as dt

timeformat = "%I:%M %p"

weatheraddr = "http://wttr.in?format=j2"

pg.init()
window = pg.display.set_mode((1024, 768))
pg.display.set_caption("Weather")

daytheme = pg.mixer.Sound("/Users/pj/Downloads/Wolf-Proj/weather/forecastday.mp3")
nighttheme = pg.mixer.Sound("/Users/pj/Downloads/Wolf-Proj/weather/forecastnight.mp3")

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

def getWeather():
    global weather
    weather = r.get(weatheraddr).json()
    global loading
    loading = False

gradient = generateGradient((0, 180, 255), (0, 180,  255))
topgradient = generateGradientHoriz((34, 139, 34), (124, 252, 0), h=64)
bottomgradient = generateGradientHoriz((240, 128, 128), (178, 34, 34), h=64)
topshadow = generateGradient((0, 0, 0), (0, 0, 0), a1=127, a2=0, h=8)

smallfont = pg.font.SysFont("Arial", 24, bold=True)
smallmedfont = pg.font.SysFont("Arial", 42, bold=True)
medfont = pg.font.SysFont("Arial", 60, bold=True)
bigfont = pg.font.SysFont("Arial", 96, bold=True)
hugefont = pg.font.SysFont("Arial", 144, bold=True)
giganticfont = pg.font.SysFont("Arial", 320, bold=True)

weatherth = th.Thread(target=getWeather)
weatherth.start()

def alphablit(surf, alpha, coord):
    transparent = pg.surface.Surface((surf.get_width(), surf.get_height())).convert_alpha()
    transparent.fill((255, 255, 255, alpha))
    transparent.blit(surf, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    window.blit(transparent, coord)

def drawshadowtext(text, size, x, y, offset, shadow=127):
    textn = size.render(text, 1, (255, 255, 255, 255))
    textsh = size.render(text, 1, (0, 0, 0, shadow))
    alphablit(textsh, shadow, (x+offset, y+offset))
    window.blit(textn, (x, y))
    return size.render(text, 1, (255, 255, 255, 255))

def drawshadowtemp(temp, size: pg.font.Font, x, y, offset, shadow=127):
    textn = size.render(temp, 1, (255, 255, 255, 255))
    textsh = size.render(temp, 1, (0, 0, 0, shadow))
    if len(temp) == 3:
        textn = pg.transform.smoothscale_by(textn, (2/3, 1))
        textsh = pg.transform.smoothscale_by(textsh, (2/3, 1))
    alphablit(textsh, shadow, (x+offset, y+offset))
    window.blit(textn, (x, y))
    return textn

def drawshadowtextcol(text, col, size, x, y, offset, shadow=127):
    textn = size.render(text, 1, col)
    textsh = size.render(text, 1, (0, 0, 0, shadow))
    alphablit(textsh, shadow, (x+offset, y+offset))
    window.blit(textn, (x, y))
    return size.render(text, 1, (255, 255, 255, 255))

def drawshadowtempcol(temp, col, size: pg.font.Font, x, y, offset, shadow=127):
    textn = size.render(temp, 1, col)
    textsh = size.render(temp, 1, (0, 0, 0, shadow))
    if len(temp) == 3:
        textn = pg.transform.smoothscale_by(textn, (2/3, 1))
        textsh = pg.transform.smoothscale_by(textsh, (2/3, 1))
    alphablit(textsh, shadow, (x+offset, y+offset))
    window.blit(textn, (x, y))
    return textn

def main():
    bottomtomorrow = False
    working = True
    playingmusic = 0
    try:
        global loading
        loading = True
    except:
        pass
    night = False
    while working:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                working = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                bottomtomorrow += 1
                if bottomtomorrow > 2:
                    bottomtomorrow = 0
        if not working:
            break
        window.blit(gradient, (0, 0))
        if loading:
            loadtext = bigfont.render("Loading...", 1, (255, 255, 255, 255))
            loadshadow = bigfont.render("Loading...", 1, (0, 0, 0, 100))
            alphablit(loadshadow, 127, (512-loadtext.get_width()/2+10, 384-loadtext.get_height()/2+10))
            window.blit(loadtext, (512-loadtext.get_width()/2, 384-loadtext.get_height()/2))
        else:
            if True:
                now = dt.datetime.now()
                sunset = dt.datetime.strptime(weather["weather"][0]["astronomy"][0]["sunset"], timeformat)
                sunrise = dt.datetime.strptime(weather["weather"][0]["astronomy"][0]["sunrise"], timeformat)
                obstime = dt.datetime.strptime(weather["current_condition"][0]["localObsDateTime"], "%Y-%m-%d %I:%M %p")
                obstimeshort = obstime.strftime("%-I:%M %p")
                
                night = False
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
                        daytheme.play(-1)
                    elif playingmusic == 2:
                        daytheme.fadeout(1000)
                        nighttheme.play(-1)
            
            currenttemp = giganticfont.render(f'{weather["current_condition"][0]["temp_F"]}', 1, (255, 255, 255, 255))
            currentcondition = smallmedfont.render(weather["current_condition"][0]["weatherDesc"][0]["value"], 1, (255, 255, 255, 255))
            location = smallmedfont.render(weather["nearest_area"][0]["areaName"][0]["value"], 1, (255, 255, 255, 255))
            alphablit(topshadow, 127, (0, 64))
            window.blit(topgradient, (0, 0))
            alphablit(topshadow, 127, (0, 524))
            window.blit(topgradient, (0, 460))
            drawshadowtext("CURRENT", smallmedfont, 5, 5, 5, 127)
            if bottomtomorrow == 0:
                drawshadowtext("TODAY", smallmedfont, 5, 465, 5, 127)
            elif bottomtomorrow == 1:
                drawshadowtext("TOMORROW", smallmedfont, 5, 465, 5, 127)
            else:
                drawshadowtext("DAY AFTER TOMORROW", smallmedfont, 5, 465, 5, 127)
            #top bar
            drawshadowtext(weather["nearest_area"][0]["areaName"][0]["value"], smallmedfont, 1024-10-location.get_width(), 5, 5, 127)
            #today
            # today's forecast (min, axg, max)
            drawshadowtemp("Today's temperatures:", smallmedfont, 5, 80, 5, 127)
            drawshadowtempcol(weather["weather"][0]["mintempF"], (135, 206, 250, 255), smallmedfont, 455, 80, 5, 127)
            drawshadowtemp(weather["weather"][0]["avgtempF"], smallmedfont, 530, 80, 5, 127)
            drawshadowtempcol(weather["weather"][0]["maxtempF"], (255, 140, 0, 255), smallmedfont, 605, 80, 5, 127)
            # current
            currenttemp = drawshadowtemp(weather["current_condition"][0]["temp_F"], giganticfont, 60, 80, 20, 180)
            drawshadowtext("°F", bigfont, currenttemp.get_width()+60, 125, 10, 160)
            drawshadowtext(f'Wind: {weather["current_condition"][0]["winddir16Point"]} @ {weather["current_condition"][0]["windspeedMiles"]}mph', smallmedfont, 540, 125, 5, 127)
            drawshadowtext(f'Humidity: {weather["current_condition"][0]["humidity"]}%', smallmedfont, 540, 175, 5, 127)
            drawshadowtext(f'Precipitation: {weather["current_condition"][0]["precipInches"]} in.', smallmedfont, 540, 225, 5, 127)
            drawshadowtext(f'Visibility: {weather["current_condition"][0]["visibilityMiles"]} mi.', smallmedfont, 540, 275, 5, 127)
            drawshadowtext(f'UV Index: {weather["current_condition"][0]["uvIndex"]}', smallmedfont, 540, 325, 5, 127)
            drawshadowtext(f'Air pressure: {weather["current_condition"][0]["pressureInches"]} inHg', smallmedfont, 540, 375, 5, 127)
            window.blit(currenttemp, (60, 80))
            drawshadowtext(weather["current_condition"][0]["weatherDesc"][0]["value"], smallmedfont, 60+currenttemp.get_width()/2-currentcondition.get_width()/2, 400, 5, 127)
            #tomorrow
            # forecasted temps
            tm1 = drawshadowtemp(weather["weather"][bottomtomorrow]["avgtempF"], bigfont, 60, 560, 10, 140)
            tm2 = drawshadowtempcol(weather["weather"][bottomtomorrow]["mintempF"], (135, 206, 250, 255), medfont, 280, 540, 7, 127)
            tm3 = drawshadowtempcol(weather["weather"][bottomtomorrow]["maxtempF"], (255, 140, 0, 255), medfont, 280, 610, 7, 127)
            drawshadowtext("°F", bigfont, tm1.get_width()+60, 560, 10, 140)
            drawshadowtextcol("°F", (135, 206, 250, 255), medfont, tm2.get_width()+280, 540, 10, 140)
            drawshadowtextcol("°F", (255, 140, 0, 255), medfont, tm3.get_width()+280, 610, 10, 140)
            # other metrics
            drawshadowtext(f'UV Index: {weather["weather"][bottomtomorrow]["uvIndex"]}', smallmedfont, 540, 540, 5, 127)
            drawshadowtext(f'Precipitation: {str(round(float(weather["weather"][bottomtomorrow]["totalSnow_cm"])*0.393701, 1))} in.', smallmedfont, 540, 590, 5, 127)
            drawshadowtext(f'Hours of Sunlight: {weather["weather"][bottomtomorrow]["sunHour"]}', smallmedfont, 540, 640, 5, 127)
            #housekeeping
            window.blit(bottomgradient, (0, 704))
            drawshadowtext(f"Last updated at {obstimeshort}", smallmedfont, 5, 768-64+5, 5, 127)
            alphablit(topshadow, 127, (0, 768-64-8))
        pg.display.flip()
main()