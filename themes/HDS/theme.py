import os
bpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blank.png")
image_replace = {
    "topgradient": bpath,
    "topgradienthealth": bpath,
    "bottomgradient": bpath,
    "topshadow": bpath,
    "bottomshadow": bpath
}
filters = [
"""
class XLFilter(TextFilter):
    def filter_pre(self, text: str, font: pg.Font, point: pg.typing.Point):
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
        grad = generateGradientHoriz((255, 255, 255), (255, 255, 255), w, h, 255, 0)
        window.blit(grad, (xx, point[1]-5))
    def filter(self, text: str, font: pg.Font, surf: pg.Surface, point: pg.typing.Point) -> pg.Surface:
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
    def filter_post(self, text: str, font: pg.Font, surf: pg.Surface, point: pg.typing.Point) -> pg.Surface:
        size = font.size(text)
        w = size[0]
        x1 = point[0]
        x2 = point[0] + w
        y = point[1] + 59
        pg.draw.line(window, (255, 255, 255), (x1, y), (x2, y), 3)
filters.append(XLFilter(pre=True, post=True))
"""
]