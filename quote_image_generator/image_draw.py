import functools
import math
import typing

from PIL import ImageDraw, ImageFont

from quote_image_generator.types import Color, Point, Size

__all__ = ("CustomImageDraw",)


class CustomImageDraw(ImageDraw.ImageDraw):

    def dashed_line(
        self,
        xy: tuple[int, int, int, int],
        fill: Color,
        dashlen: int = 4,
        ratio: int = 3,
        width: int = 1,
    ) -> None:
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

        while a0 < vlen:
            a1 = a0 + dashlen
            a1 = min(a1, vlen)
            self.line(
                (x0 + xa * a0, y0 + ya * a0, x0 + xa * a1, y0 + ya * a1), fill=fill, width=width
            )
            a0 += step

    @typing.overload
    def anchor(
        self,
        point: Point,
        size: Size,
        fill: Color = (255, 255, 255, 255),
        width: int = 1,
        style: typing.Literal["line"] = "line",
    ) -> None: ...
    @typing.overload
    def anchor(
        self,
        point: Point,
        size: Size,
        fill: Color = (255, 255, 255, 255),
        width: int = 1,
        style: typing.Literal["dashed"] = "dashed",
        dash_len: int = 4,
        dash_ratio: int = 3,
    ) -> None: ...
    def anchor(
        self,
        point: Point,
        size: Size,
        fill: Color = (255, 255, 255, 255),
        width: int = 1,
        style: typing.Literal["line", "dashed"] = "line",
        dash_len: int = 4,
        dash_ratio: int = 3,
    ) -> None:
        draw_fn = (
            self.line
            if style == "line"
            else functools.partial(
                self.dashed_line,
                dashlen=dash_len,
                ratio=dash_ratio,
            )
        )
        draw_fn(
            (point.x - size.width // 2, point.y, point.x + size.width // 2, point.y),
            fill=fill,
            width=width,
        )
        draw_fn(
            (point.x, point.y - size.height // 2, point.x, point.y + size.height // 2),
            fill=fill,
            width=width,
        )

    @typing.overload
    def grid(
        self,
        step: int = 100,
        fill: Color = (255, 255, 255, 255),
        width: int = 1,
        style: typing.Literal["line"] = "line",
    ) -> None: ...
    @typing.overload
    def grid(
        self,
        step: int = 100,
        fill: Color = (255, 255, 255, 255),
        width: int = 1,
        style: typing.Literal["dashed"] = "dashed",
        dash_len: int = 4,
        dash_ratio: int = 3,
    ) -> None: ...
    def grid(
        self,
        step: int = 100,
        fill: Color = (255, 255, 255, 255),
        width: int = 1,
        style: typing.Literal["line", "dashed"] = "line",
        dash_len: int = 4,
        dash_ratio: int = 3,
    ) -> None:
        draw_fn = (
            self.line
            if style == "line"
            else functools.partial(
                self.dashed_line,
                dashlen=dash_len,
                ratio=dash_ratio,
            )
        )

        for xi in range(0, self._image.size[0], step):
            for yi in range(0, self._image.size[1], step):
                draw_fn((xi, 0, xi, self._image.size[1]), fill=fill, width=width)
                draw_fn((0, yi, self._image.size[0], yi), fill=fill, width=width)

    def underline_text(
        self,
        xy: tuple[float, float],
        text: str,
        fill: typing.Optional[Color] = None,
        font: typing.Optional[
            typing.Union[ImageFont.ImageFont, ImageFont.FreeTypeFont, ImageFont.TransposedFont]
        ] = None,
        anchor: typing.Optional[str] = None,
        spacing: int = 4,
        align: str = "left",
        direction: typing.Optional[str] = None,
        features: typing.Optional[list[str]] = None,
        language: typing.Optional[str] = None,
        stroke_width: int = 0,
        stroke_fill: typing.Optional[Color] = None,
        embedded_color: bool = False,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        x, y, x1, y1 = self.textbbox(
            xy,
            text,
            font=font,
            anchor=anchor,
            spacing=spacing,
            align=align,
            direction=direction,
            features=features,
            language=language,
            stroke_width=stroke_width,
            embedded_color=embedded_color,
        )
        self.text(
            *args,
            xy=xy,
            text=text,
            fill=fill,
            font=font,
            anchor=anchor,
            spacing=spacing,
            align=align,
            direction=direction,
            features=features,
            language=language,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
            embedded_color=embedded_color,
            **kwargs,
        )
        line_width = math.floor(1 / 17 * abs(y1 - y)) or 1
        self.line(
            (
                x,
                y1 + 1,
                x1,
                y1 + 1,
            ),
            fill=fill,
            width=line_width,
        )

    def strikethrough_text(
        self,
        xy: tuple[float, float],
        text: str,
        fill: typing.Optional[Color] = None,
        font: typing.Optional[
            typing.Union[ImageFont.ImageFont, ImageFont.FreeTypeFont, ImageFont.TransposedFont]
        ] = None,
        anchor: typing.Optional[str] = None,
        spacing: int = 4,
        align: str = "left",
        direction: typing.Optional[str] = None,
        features: typing.Optional[list[str]] = None,
        language: typing.Optional[str] = None,
        stroke_width: int = 0,
        stroke_fill: typing.Optional[Color] = None,
        embedded_color: bool = False,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        x, y, x1, y1 = self.textbbox(
            xy,
            text,
            font=font,
            anchor=anchor,
            spacing=spacing,
            align=align,
            direction=direction,
            features=features,
            language=language,
            stroke_width=stroke_width,
            embedded_color=embedded_color,
        )
        self.text(
            *args,
            xy=xy,
            text=text,
            fill=fill,
            font=font,
            anchor=anchor,
            spacing=spacing,
            align=align,
            direction=direction,
            features=features,
            language=language,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
            embedded_color=embedded_color,
            **kwargs,
        )
        line_width = math.floor(1 / 17 * abs(y1 - y)) or 1
        self.line(
            (
                x,
                y1 - abs(y1 - y) // 2,
                x1,
                y1 - abs(y1 - y) // 2,
            ),
            fill=fill,
            width=line_width,
        )
