import math

from PIL import Image, ImageDraw


def draw_line_dashed(
    image: Image.Image,
    xy: tuple[int, int, int, int],
    dashlen: int = 4,
    ratio: int = 3,
    fill: tuple[int, int, int, int] | tuple[int, int, int] | str | None = None,
):
    x0, y0, x1, y1 = xy

    dx = x1 - x0
    dy = y1 - y0
    if dy == 0:
        vlen = dx
    elif dx == 0:
        vlen = dy
    else:
        vlen = math.sqrt(dx * dx + dy * dy)
    xa = dx / vlen
    ya = dy / vlen
    step = dashlen * ratio
    a0 = 0

    draw = ImageDraw.Draw(image)

    while a0 < vlen:
        a1 = a0 + dashlen
        a1 = min(a1, vlen)
        draw.line((x0 + xa * a0, y0 + ya * a0, x0 + xa * a1, y0 + ya * a1), fill=fill)
        a0 += step
