import typing

from PIL.Image import Image

from quote_image_generator.pipelines.base import RedirectKeywordPipeLine
from quote_image_generator.types import DrawEntity, InputEntity, SizeBox

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
        input_text: str | None = None,
        input_enitites: list[InputEntity] | None = None,
        draw_entities: list[DrawEntity] | None = None,
        max_font_size: int = 128,
        **kwargs,
    ) -> None | dict[str, typing.Any]:
        if input_text:
            entities = generator.entities_processor.convert_input_to_draw_entity(
                input_text,
                input_enitites or [],
            )
        else:
            entities = draw_entities

        if entities is None:
            raise ValueError("Entities must be set")

        font_size, text_size = generator.text_processor.get_entities_size(
            entities, box, max_font_size
        )

        generator.text_processor.draw_entities(
            im,
            entities,
            box,
            horizontal_align=horizontal_align,
            vertical_align=vertical_align,
            max_font_size=max_font_size,
        )
