import typing

from PIL import Image, ImageColor, ImageDraw

from quote_image_generator.pipelines.base import BasePipeLine
from quote_image_generator.types import Color

if typing.TYPE_CHECKING:
    from quote_image_generator.generator import QuoteGenerator


class StaticColorBackgroundPipeLine(BasePipeLine):

    def pipe(
        self,
        im: Image.Image,
        generator: "QuoteGenerator",
        *,
        background_color: Color,
        **kwargs,
    ) -> None:
        im.paste(Image.new("RGBA", im.size, background_color))


class GradientBackgroundPipeLine(BasePipeLine):
    """thx https://github.com/hexvel

    https://github.com/hexvel/gradient-background/blob/main/test.py
    """

    def pipe(
        self,
        im: Image.Image,
        generator: "QuoteGenerator",
        *,
        background_from_color: Color,
        background_to_color: Color,
        background_direction: typing.Literal["l-r", "t-b", "lt-rb", "rt-lb"] = "t-b",
        **kwargs,
    ) -> None:
        width, height = im.size
        background_from_color = self._parse_color(background_from_color)
        background_to_color = self._parse_color(background_to_color)

        gradient = self._create_gradient(
            width, height, background_from_color, background_to_color, background_direction
        )
        im.paste(gradient, (0, 0), gradient)

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
