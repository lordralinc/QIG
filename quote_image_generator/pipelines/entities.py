import typing

from PIL.Image import Image

from quote_image_generator.image_draw import CustomImageDraw
from quote_image_generator.pipelines.base import RedirectKeywordPipeLine
from quote_image_generator.types import DrawEntity, InputEntity, Point, Size, SizeBox

__all__ = ("EntitiesPipeLine",)

if typing.TYPE_CHECKING:
    from quote_image_generator.generator import QuoteGenerator


class EntitiesPipeLine(RedirectKeywordPipeLine):
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
