import io
import math
import pathlib
import typing

from PIL import Image, ImageDraw, ImageFont

from quote_image_generator.processors.emoji import ABCEmojiSource
from quote_image_generator.types import (
    DrawEntity,
    Point,
    Size,
    SizeBox,
    TextDrawEntity,
)

__all__ = ("TextProcessor",)


PIL_ANCHOR_SIZE = 2


class TextProcessor:

    def __init__(self, emoji_source: ABCEmojiSource) -> None:
        self.emoji_source = emoji_source

    def get_line_size_by_box(
        self,
        text: str,
        max_box_size: Size,
        font_path: pathlib.Path | str,
        max_font_size: int,
    ) -> tuple[int, Size]:

        emojies = self.emoji_source.get_emojies(text)

        for emoji in emojies:
            text = text.replace(emoji, "", 1)
        font_path = font_path if isinstance(font_path, str) else str(font_path.absolute())

        for size in range(max_font_size, 0, -1):
            font = ImageFont.truetype(font_path, size=size, encoding="utf-8")
            text_size = Size(math.floor(font.getlength(text)), size)
            text_size = Size(
                width=text_size.width
                + math.floor(len(emojies) * size * self.emoji_source.emoji_scale),
                height=size,
            )

            if text_size.width <= max_box_size.width and text_size.height <= max_box_size.height:
                return size, text_size
        raise ValueError(
            f"Unable to fit text '{text}' within the box constraints {max_box_size} using any font size up to {max_font_size}."
        )

    def _redirect_position_by_anchor(
        self,
        image: Image.Image,
        anchor: Point,
        font: str,
        font_size: int,
        pil_anchor: str = "lm",
    ) -> Point:
        if len(pil_anchor) != PIL_ANCHOR_SIZE:
            raise ValueError("Invalid anchor string")

        img_font = ImageFont.truetype(font, size=font_size, encoding="utf-8")

        ascent, descent = img_font.getmetrics()

        new_anchor = Point(anchor.x, anchor.y)

        if pil_anchor[0] == "m":
            new_anchor = Point(anchor.x - image.size[0] // 2, anchor.y)
        if pil_anchor[0] == "r":
            new_anchor = Point(anchor.x - image.size[0], anchor.y)

        if pil_anchor[1] == "a":
            new_anchor = Point(new_anchor.x, anchor.y + (ascent - image.size[1]))
        if pil_anchor[1] == "m":
            new_anchor = Point(new_anchor.x, anchor.y - (image.size[1] // 2))
        if pil_anchor[1] in ("s", "b"):
            new_anchor = Point(new_anchor.x, anchor.y - (image.size[1]))
        if pil_anchor[1] in "d":
            new_anchor = Point(new_anchor.x, anchor.y - (image.size[1] + descent))
        return new_anchor

    def draw_single_line(
        self,
        image: Image.Image | ImageDraw.ImageDraw,
        anchor: Point,
        entity: TextDrawEntity,
        font_size: int,
        emoji_size: int,
        pil_anchor: str = "lm",
    ):
        draw = image if isinstance(image, ImageDraw.ImageDraw) else ImageDraw.Draw(image)
        font = ImageFont.truetype(
            entity["font"],
            size=font_size,
            encoding="utf-8",
        )
        current_position = Point(anchor.x, anchor.y)
        for chunk in self.emoji_source.chunk_by_emoji(entity["content"]):
            if chunk["type"] == "emoji":
                emoji_image = self.emoji_source.get_image(chunk["content"]).resize(
                    (emoji_size, emoji_size),
                    Image.Resampling.LANCZOS,
                )
                draw._image.paste(
                    emoji_image,
                    self._redirect_position_by_anchor(
                        emoji_image,
                        current_position,
                        font=entity["font"],
                        font_size=font_size,
                        pil_anchor=pil_anchor,
                    ),
                    emoji_image.convert("RGBA"),
                )
                current_position = Point(current_position.x + emoji_size, current_position.y)
                continue
            length = math.ceil(font.getlength(chunk["content"]))
            draw.text(
                current_position,
                chunk["content"],
                font=font,
                fill=entity["color"],
                anchor=pil_anchor,
            )
            current_position = Point(current_position.x + length, current_position.y)

    def get_entities_size(
        self, entities: list[DrawEntity], max_box_size: SizeBox, max_font_size: int
    ) -> tuple[int, Size]:
        for size in range(max_font_size, 1, -1):
            max_current_size = Size(0, size)
            current_position = Point(0, 0)
            for entity in entities:
                if entity["type"] == "emoji":
                    current_position = Point(
                        current_position.x + math.floor(size * self.emoji_source.emoji_scale),
                        current_position.y,
                    )
                elif entity["type"] == "new_line":
                    current_position = Point(0, current_position.y + size)
                elif entity["type"] in (
                    "default",
                    "italic",
                    "code",
                    "bold",
                    "link",
                    "underline",
                    "code_block",
                    "quote",
                ):
                    content = entity["content"]

                    emojies = self.emoji_source.get_emojies(content)
                    for emoji in emojies:
                        content = content.replace(emoji, "", 1)

                    font = ImageFont.truetype(entity["font"], size=size, encoding="utf-8")
                    text_size = Size(math.floor(font.getlength(content)), size)
                    text_size = Size(
                        width=text_size.width
                        + math.floor(len(emojies) * size * self.emoji_source.emoji_scale),
                        height=size,
                    )
                    current_position = Point(
                        current_position.x + text_size.width, current_position.y
                    )
                else:
                    typing.assert_never(entity["type"])

                max_current_size = Size(
                    max(max_current_size.width, current_position.x),
                    max(max_current_size.height, current_position.y + size),
                )
            if (
                max_current_size.width <= max_box_size.width
                and max_current_size.height <= max_box_size.height
            ):
                return size, max_current_size

        raise ValueError(
            f"Unable to fit entities within the box constraints {max_box_size} using any font size up to {max_font_size}."
        )

    def draw_entities(
        self,
        image: Image.Image | ImageDraw.ImageDraw,
        entities: list[DrawEntity],
        box: SizeBox,
        horizontal_align: typing.Literal["left", "middle", "right"],
        vertical_align: typing.Literal["top", "middle", "bottom"],
        max_font_size: int = 128,
    ) -> None:

        image = image if isinstance(image, Image.Image) else image._image
        draw = ImageDraw.Draw(image)

        font_size, entities_size = self.get_entities_size(
            entities, box, max_font_size=max_font_size
        )

        delta_x = box.width - entities_size.width
        delta_y = box.height - entities_size.height

        anchor = Point(box.x, box.y)  # left, top

        if horizontal_align == "middle":
            anchor = Point(anchor.x + delta_x // 2, anchor.y)
        if horizontal_align == "right":
            anchor = Point(anchor.x + delta_x, anchor.y)
        if vertical_align == "middle":
            anchor = Point(anchor.x, anchor.y + delta_y // 2)
        if vertical_align == "bottom":
            anchor = Point(anchor.x, anchor.y + delta_y)

        current_position = Point(anchor.x, anchor.y)

        for entity in entities:
            if entity["type"] == "emoji":
                emoji_image = (
                    Image.open(io.BytesIO(entity["emoji_image"]))
                    .convert("RGBA")
                    .resize(
                        (
                            math.floor(font_size * self.emoji_source.emoji_scale),
                            math.floor(font_size * self.emoji_source.emoji_scale),
                        ),
                        resample=Image.Resampling.LANCZOS,
                    )
                )
                image.paste(
                    emoji_image,
                    current_position,
                    emoji_image,
                )
                current_position = Point(current_position.x + font_size, current_position.y)
            elif entity["type"] == "new_line":
                current_position = Point(anchor.x, current_position.y + font_size)
            elif entity["type"] in (
                "default",
                "italic",
                "code",
                "bold",
                "link",
                "underline",
                "code_block",
                "quote",
            ):
                font = ImageFont.truetype(
                    entity["font"],
                    size=font_size,
                    encoding="utf-8",
                )
                emoji_size = math.floor(font_size * self.emoji_source.emoji_scale)
                for chunk in self.emoji_source.chunk_by_emoji(entity["content"]):
                    if chunk["type"] == "emoji":

                        emoji_image = (
                            self.emoji_source.get_image(chunk["content"])
                            .resize(
                                (emoji_size, emoji_size),
                                resample=Image.Resampling.LANCZOS,
                            )
                            .convert("RGBA")
                        )
                        image.paste(
                            emoji_image,
                            current_position,
                            emoji_image,
                        )
                        current_position = Point(
                            current_position.x + emoji_size,
                            current_position.y,
                        )
                    else:
                        draw.text(
                            current_position,
                            chunk["content"],
                            font=font,
                            fill=entity["color"],
                        )
                        current_position = Point(
                            current_position.x + math.ceil(font.getlength(chunk["content"])),
                            current_position.y,
                        )
