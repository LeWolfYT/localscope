import os
bpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blank.png")
gpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bottomgradient.png")
lpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ldlgradient.png")
image_replace = {
    "topgradient": bpath,
    "topgradientred": bpath,
    "topgradienthealth": bpath,
    "topgradientcustom": bpath,
    "bottomgradient": gpath,
    "bottomgradientred": gpath,
    "ldlgradient": lpath,
    "topshadow": bpath,
    "bottomshadow": bpath
}
filters = ["""
class IntelliFilter(TextFilter):
    def filter_pre(self, text: str, font: pg.Font, point: pg.typing.Point, alpha: int):
        if len(text.split(" ")) > 1:
            texttochange = text.split(" ")[1]
            texttoskip = text.split(" ")[0] + " "
            w = font.size(texttochange)[0]
            h = 64
            xx = point[0] + font.size(texttoskip)[0]
        else:
            w = font.size(text)[0]
            h = 64
            xx = point[0]
        grad = generateGradientHoriz((255, 255, 255), (255, 255, 255), w, h, alpha, 0)
        window.blit(grad, (xx, point[1]-5))
    def filter(self, text: str, font: pg.Font, surf: pg.Surface, point: pg.typing.Point, alpha: int) -> pg.Surface:
        surf2 = surf.copy()
        if len(text.split(" ")) > 1:
            texttochange = text.split(" ")[1]
            texttoskip = text.split(" ")[0] + " "
            w = font.size(texttochange)[0]
            xx = font.size(texttoskip)[0]
        else:
            xx = 0
            w = surf.get_width()
        surf2.fill((0, 0, 0, 255), pg.Rect(xx, 0, w, surf.get_height()), pg.BLEND_RGBA_MULT)
        return surf2
    def filter_post(self, text: str, font: pg.Font, surf: pg.Surface, point: pg.typing.Point, alpha: int) -> pg.Surface:
        size = font.size(text)
        w = size[0]
        x1 = point[0]
        x2 = point[0] + w
        y = point[1] + 59
        pg.draw.line(window, (255, 255, 255, alpha), (x1, y), (x2, y), 3)
filters["title"].append(IntelliFilter(pre=True, post=True))""",
"""class LDLFilter(TextFilter):
    def filter(self, text: str, font: pg.Font, surf: pg.Surface, point: pg.typing.Point, alpha: int) -> pg.Surface:
        surf2 = surf.copy()
        xx = 0
        w = surf.get_width()
        if w > 1366/2:
            w = 1366/2
        surf2.fill((0, 0, 0, 255), pg.Rect(xx, 0, w, surf.get_height()), pg.BLEND_RGBA_MULT)
        return surf2
filters["tickerleft"].append(LDLFilter())
filters["tickertr"].append(LDLFilter())
"""
]