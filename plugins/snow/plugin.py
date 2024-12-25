import os
snowpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snow.gif")
init = """
global snowsurf
global snow_y
snowsurf = pg.image.load("{}")
snow_y = 0
""".format(snowpath)

actions = {
    "pre": ["""
global snowsurf
global snow_y
snow_y += 1
if snow_y > snowsurf.get_height():
    snow_y = 0
needed = math.ceil(screenwidth / snowsurf.get_width())
neededy = math.ceil(768 / snowsurf.get_height())
for i in range(needed):
    for j in range(neededy):
        window.blit(snowsurf, (i * snowsurf.get_width(), j * snowsurf.get_height() + snow_y))
        window.blit(snowsurf, (i * snowsurf.get_width(), -j * snowsurf.get_height() + snow_y))
"""]
}