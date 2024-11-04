import typing

from PIL.Image import Image

from quote_image_generator.image_draw import CustomImageDraw
from quote_image_generator.pipelines.base import RedirectKeywordPipeLine
from quote_image_generator.types import DrawEntity, InputEntity, Point, Size, SizeBox

__all__ = ("EntitiesPipeLine",)

if typing.TYPE_CHECKING:
    from quote_image_generator.generator import QuoteGenerator


class EntitiesPipeLine(RedirectKeywordPipeLine):
    """
    `EntitiesPipeLine` is a pipeline class designed to draw entities (text and related visual elements)
    within a specified area on an image. It allows detailed configuration of text positioning,
    alignment, and scaling to fit the defined bounding box. This pipeline is ideal for applications
    that need precise text placement and layout customization.

    Class Variables:
    - `REQUIRED_ARGS` (list[str]): Specifies "box" as a required argument.
    - `OPTIONAL_ARGS` (list[str]): Defines optional arguments, including:
        - `vertical_align`, `horizontal_align`: Control the alignment of entities within the box.
        - `input_text`: Text to convert into drawable entities.
        - `input_entities`, draw_entities: Input or pre-drawn entities for customization.
        - `max_font_size`: Maximum font size for drawing entities.

    Parameters:
    - `box` (SizeBox): The bounding box where entities will be drawn.
    - `vertical_align` (Literal["top", "middle", "bottom"]): Vertical alignment of entities within the box.
    - `horizontal_align` (Literal["left", "middle", "right"]): Horizontal alignment of entities within the box.
    - `input_text` (Optional[str]): Text content to convert into drawable entities if provided.
    - `input_entities` (Optional[list[InputEntity]]): List of input entities for custom drawing.
    - `draw_entities` (Optional[list[DrawEntity]]): List of pre-created drawable entities to render.
    - `max_font_size` (int): Maximum font size allowed for entities. Defaults to 128.
    - `debug` (bool): When True, renders an anchor marker at the box origin for alignment reference.

    Methods:
    - `_pipe`: Converts input text to entities or directly draws given entities within the box.
      Aligns entities based on the specified parameters and optionally marks the anchor for debugging.
    """

    REQUIRED_ARGS: typing.ClassVar[list[str]] = ["box"]
    OPTIONAL_ARGS: typing.ClassVar[list[str]] = [
        "vertical_align",
        "horizontal_align",
        "input_text",
        "input_enitites",
        "draw_entities",
        "max_font_size",
    ]

    def _pipe(
        self,
        im: Image,
        generator: "QuoteGenerator",
        *,
        box: SizeBox,
        vertical_align: typing.Literal["top", "middle", "bottom"] = "middle",
        horizontal_align: typing.Literal["left", "middle", "right"] = "middle",
        input_text: typing.Optional[str] = None,
        input_enitites: typing.Optional[list[InputEntity]] = None,
        draw_entities: typing.Optional[list[DrawEntity]] = None,
        max_font_size: int = 128,
        debug: bool = False,
        **kwargs,
    ) -> None:
        if input_text:
            entities = generator.entities_processor.convert_input_to_draw_entity(
                input_text,
                input_enitites or [],
            )
        else:
            entities = draw_entities

        if entities is None:
            raise ValueError("Entities must be set")

        generator.text_processor.draw_entities(
            im,
            entities,
            box,
            horizontal_align=horizontal_align,
            vertical_align=vertical_align,
            max_font_size=max_font_size,
        )
        if debug:
            draw = CustomImageDraw(im)
            draw.anchor(Point(box.x, box.y), Size(50, 50), fill=(255, 0, 0, 75))
