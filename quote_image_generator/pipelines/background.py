import typing

import typing_extensions
from PIL import Image, ImageColor, ImageDraw

from quote_image_generator.image_draw import CustomImageDraw
from quote_image_generator.pipelines.base import BasePipeLine
from quote_image_generator.types import Color

if typing.TYPE_CHECKING:
    from quote_image_generator.generator import QuoteGenerator


class _StaticColorBackgroundPipeLineKwargs(typing.TypedDict):
    background_color: typing_extensions.NotRequired[Color]


class StaticColorBackgroundPipeLine(BasePipeLine):
    """
    `StaticColorBackgroundPipeLine` is a pipeline class used to apply a solid color background
    to an image. It allows the user to specify a color to be used as the background and provides
    an optional debugging mode that overlays a grid on top of the background for alignment and
    positioning reference.

    Parameters:
    - `background_color` (Color): The color to fill the background.
    - `debug` (bool): Enables a grid overlay in a semi-transparent, dashed style if set to True.

    Methods:
    - `pipe`: Applies the specified solid color as the background of the image. If debug is enabled,
      adds a grid overlay on top of the color for visual aid during development.
    """

    def __init__(
        self, **kwargs: typing_extensions.Unpack[_StaticColorBackgroundPipeLineKwargs]
    ) -> None:
        super().__init__(**kwargs)

    def pipe(
        self,
        im: Image.Image,
        generator: "QuoteGenerator",
        *,
        background_color: Color,
        debug: bool,
        **kwargs,
    ) -> None:
        im.paste(Image.new("RGBA", im.size, background_color))
        if debug:
            draw = CustomImageDraw(im)
            draw.grid(fill=(0, 255, 0, 75), style="dashed")


class _GradientBackgroundPipeLineKwargs(typing.TypedDict):
    background_from_color: typing_extensions.NotRequired[Color]
    background_to_color: typing_extensions.NotRequired[Color]
    background_direction: typing_extensions.NotRequired[Color]


class GradientBackgroundPipeLine(BasePipeLine):
    """
    GradientBackgroundPipeLine is a pipeline class designed to apply a smooth color gradient
    as a background on an image. It supports customizable gradient transitions between two colors,
    with options for direction. This allows for creating visually engaging backgrounds that blend
    seamlessly from one color to another.

    Parameters:
    - `background_from_color` (Color): The starting color of the gradient.
    - `background_to_color` (Color): The ending color of the gradient.
    - `background_direction` (str): Specifies the direction of the gradient. Options include:
      - "l-r": Left to Right
      - "t-b": Top to Bottom
      - "lt-rb": Left-Top to Right-Bottom (diagonal)
      - "rt-lb": Right-Top to Left-Bottom (diagonal)
    - `debug` (bool): When set to True, overlays a semi-transparent dashed grid for alignment assistance.

    Methods:
    - `pipe`: Applies the gradient background to the image based on specified colors and direction.
      If debug mode is active, it overlays a grid for visual reference during adjustments.

    Internal Methods:
    - `_create_gradient`: Generates a gradient image in the specified direction.
    - `_blend_colors`: Blends two colors based on a blending factor.
    - `_parse_color`: Parses the color input to ensure compatibility with RGBA format.

    Example:
        ```
        background = GradientBackgroundPipeLine(
            background_from_color="blue",
            background_to_color="green",
            background_direction="l-r"
        )
        ```

    Thanks:
        https://github.com/hexvel
    """

    def __init__(
        self, **kwargs: typing_extensions.Unpack[_GradientBackgroundPipeLineKwargs]
    ) -> None:
        super().__init__(**kwargs)

    def pipe(
        self,
        im: Image.Image,
        generator: "QuoteGenerator",
        *,
        background_from_color: Color,
        background_to_color: Color,
        background_direction: typing.Literal["l-r", "t-b", "lt-rb", "rt-lb"] = "t-b",
        debug: bool = False,
        **kwargs,
    ) -> None:
        width, height = im.size
        background_from_color = self._parse_color(background_from_color)
        background_to_color = self._parse_color(background_to_color)

        gradient = self._create_gradient(
            width, height, background_from_color, background_to_color, background_direction
        )
        im.paste(gradient, (0, 0), gradient)
        if debug:
            draw = CustomImageDraw(im)
            draw.grid(fill=(0, 255, 0, 75), style="dashed")

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
