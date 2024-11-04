import math
import typing

from PIL.Image import Image

from quote_image_generator.image_draw import CustomImageDraw
from quote_image_generator.pipelines.base import RedirectKeywordPipeLine
from quote_image_generator.types import Color, FontSet, Point, Size, SizeBox, TextDrawEntity

if typing.TYPE_CHECKING:
    from quote_image_generator.generator import QuoteGenerator

__all__ = ("TextPipeLine",)


class TextPipeLine(RedirectKeywordPipeLine):
    """
    `TextPipeLine` is a pipeline class for rendering text within a defined area on an image.
    It supports flexible positioning, alignment, and font scaling, allowing for dynamic text
    overlay that adapts to the specified bounding box and alignment options.

    Class Variables:
    - `REQUIRED_ARGS` (list[str]): Specifies "content" and "box" as required arguments.
    - `OPTIONAL_ARGS` (list[str]): Defines optional arguments, including:
        - `color`: Sets the color of the text (default is white).
        - `font`: Specifies the font style, which can be a path or a callable for font selection.
        - `vertical_align`, `horizontal_align`: Control text alignment within the box.
        - `max_font_size`: Limits the maximum font size for fitting the text within the box.

    Parameters:
    - `content` (str): The text content to display within the bounding box.
    - `box` (SizeBox): The bounding area on the image where text will be rendered.
    - `color` (Color): Text color as an RGB or RGBA tuple. Defaults to white (255, 255, 255).
    - `font` (Union[str, Callable[[FontSet], str]]): Font file path or a callable for dynamic font selection.
    - `vertical_align` (Literal["top", "middle", "bottom"]): Specifies vertical alignment of the text.
    - `horizontal_align` (Literal["left", "middle", "right"]): Specifies horizontal alignment of the text.
    - `max_font_size` (int): Maximum font size for scaling text within the box.
    - `debug` (bool): When True, displays a marker at the top-left corner of the box for alignment debugging.

    Methods:
    - `_pipe`: Positions and draws the text within the box, applying scaling to fit the content
      according to the specified maximum font size. Adjusts alignment based on parameters
      and draws the text on the image.

    Example:
        ```
        pipeline = TextPipeLine(content="Sample Text", box=some_box, color=(0, 0, 0), max_font_size=100)
        pipeline.pipe(im, generator)
        ```
    """

    REQUIRED_ARGS: typing.ClassVar[list[str]] = [
        "content",
        "box",
    ]
    OPTIONAL_ARGS: typing.ClassVar[list[str]] = [
        "color",
        "font",
        "vertical_align",
        "horizontal_align",
        "max_font_size",
    ]

    def _pipe(
        self,
        im: Image,
        generator: "QuoteGenerator",
        *,
        content: str,
        box: SizeBox,
        color: Color = (255, 255, 255),
        font: typing.Union[str, typing.Callable[[FontSet], str]] = lambda fontset: fontset.bold,
        vertical_align: typing.Literal["top", "middle", "bottom"] = "middle",
        horizontal_align: typing.Literal["left", "middle", "right"] = "middle",
        max_font_size: int = 128,
        debug: bool = False,
        **kwargs,
    ) -> None:
        if not isinstance(font, str):
            font = font(generator.entities_processor.fontset)
        font_size, text_size = generator.text_processor.get_line_size_by_box(
            content,
            box.size,
            font_path=font,
            max_font_size=max_font_size,
        )

        delta = Point(box.width - text_size.width, box.height - text_size.height)
        position = Point(box.x, box.y)

        if horizontal_align == "middle":
            position = Point(position.x + delta.x // 2, position.y)
        if horizontal_align == "right":
            position = Point(position.x + delta.x, position.y)
        if vertical_align == "middle":
            position = Point(position.x, position.y + delta.y // 2)
        if vertical_align == "bottom":
            position = Point(position.x, position.y + delta.y)

        generator.text_processor.draw_single_line(
            im,
            position,
            TextDrawEntity(
                type="default",
                offset=0,
                length=len(content),
                content=content,
                font=font,
                color=color,
            ),
            font_size=font_size,
            emoji_size=math.floor(font_size * generator.text_processor.emoji_source.emoji_scale),
        )
        if debug:
            draw = CustomImageDraw(im)
            draw.anchor(Point(box.x, box.y), Size(50, 50), fill=(255, 0, 0, 75))
