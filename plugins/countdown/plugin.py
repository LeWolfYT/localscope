import os
apath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand.png")

fixtures = [
"""
today = dt.date.today()
target = dt.date(2024, 12, 25)
delta = target.day - today.day
drawshadowtext(str(delta) + (" days" if delta != 1 else " day"), smallmedfont, screenwidth - smallmedfont.size(str(delta) + (" days" if delta != 1 else " day"))[0] - 5, 5, 5)
"""
]