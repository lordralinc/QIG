import typing

from PIL import Image, ImageColor, ImageDraw

from QIG.layers.base import BaseLayer
from QIG.types import Color

if typing.TYPE_CHECKING:
    from QIG.generator import QuoteGenerator


class StaticColorBackgroundLayer(BaseLayer):

    def pipe(
        self,
        im: Image.Image,
        generator: "QuoteGenerator",
        *,
        background_color: Color,
        **kwargs,
    ) -> None:
        im.paste(Image.new("RGBA", im.size, background_color))


class GradientBackgroundLayer(BaseLayer):

    def pipe(
        self,
        im: Image.Image,
        from_color: Color,
        to_color: Color,
        direction: typing.Literal["l-r", "t-b", "lt-rb", "rt-lb"] = "t-b",
        **kwargs,
    ) -> Image.Image:
        width, height = im.size
        from_color = self._parse_color(from_color)
        to_color = self._parse_color(to_color)

        gradient = self._create_gradient(width, height, from_color, to_color, direction)
        im.paste(gradient, (0, 0), gradient)
        return im

    def _create_gradient(
        self,
        width: int,
        height: int,
        from_color: tuple[int, int, int, int],
        to_color: tuple[int, int, int, int],
        direction: str,
    ) -> Image.Image:
        gradient = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(gradient)

        if direction == "l-r":
            for x in range(width):
                color = self._blend_colors(from_color, to_color, x / width)
                draw.line([(x, 0), (x, height)], fill=color)

        elif direction == "t-b":
            for y in range(height):
                color = self._blend_colors(from_color, to_color, y / height)
                draw.line([(0, y), (width, y)], fill=color)

        elif direction in {"lt-rb", "rt-lb"}:
            for y in range(height):
                for x in range(width):
                    blend = (
                        (x + y) / (width + height)
                        if direction == "lt-rb"
                        else (width - x + y) / (width + height)
                    )
                    color = self._blend_colors(from_color, to_color, blend)
                    draw.point((x, y), fill=color)

        return gradient

    def _blend_colors(
        self,
        from_color: tuple[int, int, int, int],
        to_color: tuple[int, int, int, int],
        blend: float,
    ) -> tuple[int, int, int, int]:
        return tuple(int(fc + (tc - fc) * blend) for fc, tc in zip(from_color, to_color))  # type: ignore

    def _parse_color(self, color: Color) -> tuple[int, int, int, int]:
        if isinstance(color, str):
            return (*ImageColor.getrgb(color), 255)  # type: ignore
        elif len(color) == 3:  # noqa: PLR2004
            return (*color, 255)
        return color
