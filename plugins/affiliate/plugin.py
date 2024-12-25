import os
apath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand.png")

init = """
global affiliatesurf
affiliatesurf = pg.image.load("{}")
ah = affiliatesurf.get_height()
aw = affiliatesurf.get_width()
affiliatesurf = pg.transform.smoothscale(affiliatesurf, (round(aw/ah*64), 64))
""".format(apath)

fixtures = [
"""
global affiliatesurf
window.blit(affiliatesurf, (screenwidth-affiliatesurf.get_width(), 0))
"""
]