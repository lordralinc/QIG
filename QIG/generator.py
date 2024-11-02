import functools
import io
import math
import os
import pathlib
import re
import typing

from PIL import Image, ImageDraw, ImageFont

from QIG.processors.emoji import ABCEmojiSource, FileEmojiSource
from QIG.processors.text_processor import TextProcessor
from QIG.types import (
    ColorSet,
    DrawEntity,
    EmojiDrawEntity,
    FontSet,
    Grid,
    InputEntity,
    NewLineDrawEntity,
    Point,
    Size,
    SizeBox,
    TextDrawEntity,
    type_cast,
)
from QIG.utils import draw_line_dashed


class QuoteGenerator:

    base_image: Image.Image
    author_image_type: typing.Literal["circle", "rounded", "square"]

    def __init__(
        self,
        fontset: FontSet,
        grid: Grid,
        colorset: ColorSet,
        bi: bytes | Image.Image | tuple[int, int],
        author_image_type: typing.Literal["circle", "rounded", "square"] = "circle",
        emoji_scale: float = 1.3,
        emoji_dir: pathlib.Path = pathlib.Path("emoji"),
        # TEXT PROCESSOR CONFIG
        max_font_size: int = 128,
        *,
        debug: bool = os.environ.get("QUOTE_GENERATOR_DEBUG", "False") == "True",
        text_processor_cls: type[TextProcessor] | None = None,
        emoji_source: ABCEmojiSource | None = None,
    ) -> None:
        self.fontset = fontset
        self.grid = grid
        self.colorset = colorset
        self.base_image = (
            bi
            if isinstance(bi, Image.Image)
            else (
                Image.new("RGBA", bi)
                if isinstance(bi, tuple)
                else Image.open(io.BytesIO(bi)).convert("RGBA")
            )
        )
        self.debug = debug

        self.author_image_type = author_image_type
        self.emoji_scale = emoji_scale

        self.emoji_dir = emoji_dir

        self.max_font_size = max_font_size

        self.emoji_source = emoji_source or FileEmojiSource()
        self.text_processor = (text_processor_cls or TextProcessor)(self)

    @functools.cached_property
    def emoji_table(self) -> dict[str, pathlib.Path]:
        return {
            "".join(chr(int(code, 16)) for code in it.stem.replace("U+", "").split()): it
            for it in self.emoji_dir.glob("*.png")
        }

    @functools.cached_property
    def emoji_regex(self) -> typing.Pattern:
        emoji_patterns = sorted(self.emoji_table.keys(), key=len, reverse=True)
        regex_pattern = "|".join(map(re.escape, emoji_patterns))
        return re.compile(f"({regex_pattern})")

    def get_singleline_text_size(
        self, text: str, font: str, max_font_size: int, max_box_size: Size
    ) -> tuple[int, Point]:

        for size in range(max_font_size, 0, -1):
            ttf_font = ImageFont.truetype(font, size=size, encoding="utf-8")
            bbox = ttf_font.getbbox(text)

            box_x, box_y = abs(bbox[2] - bbox[0]), abs(bbox[3] - bbox[1])

            if box_x < max_box_size.width and box_y < max_box_size.height:
                return max_font_size, Point(int(box_x), int(box_y))
            max_font_size -= 1
        raise ValueError(
            f"Unable to fit text '{text}' within the box constraints {max_box_size} using any font size up to {max_font_size}."
        )

    def split_new_line_content(self, entity: DrawEntity) -> list[DrawEntity]:
        entities: list[DrawEntity] = []
        content = entity.get("content", "")
        if "\n" not in content:
            return [entity]

        lines = content.split("\n")
        current_offset = entity["offset"]

        for index, line in enumerate(lines, 1):
            if line:
                ent = type_cast(entity, TextDrawEntity)
                entities.append(
                    TextDrawEntity(
                        type=ent["type"],
                        font=ent["font"],
                        color=ent["color"],
                        content=line,
                        offset=current_offset,
                        length=len(line),
                    )
                )
                current_offset += len(line)

            if index != len(lines):
                entities.append(
                    NewLineDrawEntity(
                        type="new_line",
                        offset=current_offset,
                        length=1,
                    )
                )
                current_offset += 1

        return entities

    def _create_text_entities(
        self, text: str, entity: InputEntity, font_table: dict
    ) -> list[DrawEntity]:
        content = text[entity["offset"] : entity["offset"] + entity["length"]]
        color = (
            self.colorset.code
            if entity["type"] in ("code", "code_block")
            else (self.colorset.link if entity["type"] == "link" else self.colorset.content)
        )
        font = font_table.get(entity["type"], self.fontset.default)

        text_entity = TextDrawEntity(
            type=entity["type"],
            font=font,
            color=color,
            content=content,
            offset=entity["offset"],
            length=len(content),
        )
        return self.split_new_line_content(text_entity)

    def _create_default_entities(self, text: str, start: int, end: int) -> list[DrawEntity]:
        content = text[start:end]
        default_entity = TextDrawEntity(
            type="default",
            content=content,
            offset=start,
            length=len(content),
            font=self.fontset.default,
            color=self.colorset.content,
        )
        return self.split_new_line_content(default_entity)

    def get_draw_entities(self, text: str, entities: list[InputEntity]) -> list[DrawEntity]:

        font_table = {
            "bold": self.fontset.bold,
            "italic": self.fontset.italic,
            "code": self.fontset.mono,
            "code_block": self.fontset.mono,
            "link": self.fontset.italic,
            "underline": self.fontset.default,
        }

        draw_entities = []
        index = 0
        while index < len(text):
            entity_found = False
            for entity in entities:
                if entity["offset"] <= index < entity["offset"] + entity["length"]:
                    entity_found = True
                    if entity["type"] in font_table:
                        draw_entities.extend(self._create_text_entities(text, entity, font_table))
                    elif entity["type"] == "emoji":
                        ent = type_cast(entity, EmojiDrawEntity)
                        draw_entities.append({**ent, "emoji_image": ent["emoji_image"]})
                    index += entity["length"]
                    break
            if not entity_found:
                next_offset = min(
                    (e["offset"] for e in entities if e["offset"] > index),
                    default=len(text),
                )
                draw_entities.extend(self._create_default_entities(text, index, next_offset))
                index = next_offset

        return draw_entities

    def get_title_layer(self, text: str) -> Image.Image:
        image = Image.new("RGBA", self.base_image.size, color=(0, 0, 0, 0))
        font_size, size = self.text_processor.get_line_size_by_box(
            text,
            font_path=self.fontset.bold,
            max_font_size=128,
            max_box_size=self.grid.title_box.size,
        )

        position = Point(
            self.grid.title_box.x + (self.grid.title_box.width // 2 - size.width // 2),
            self.grid.title_box.y,
        )

        self.text_processor.draw_single_line(
            image,
            anchor=position,
            entity=TextDrawEntity(
                type="bold",
                offset=0,
                length=len(text),
                content=text,
                font=self.fontset.bold,
                color=self.colorset.title,
            ),
            font_size=font_size,
            emoji_size=math.floor(size.height * self.emoji_scale),
            pil_anchor="lt",
        )

        self._dbg_draw_anchor(
            image,
            position,
            Point(200, 200),
            fill=(255, 0, 0, 75),
            title=f"title-anchor {position}",
        )
        self._dbg_draw_bbox(
            image,
            self.grid.title_box,
            title="title-box " + str(self.grid.title_box.to_point_box()),
            fill=(0, 0, 255, 75),
        )

        return image

    def get_entities_fontsize(
        self, enitites: list[DrawEntity], max_size: int, max_box_size: Size
    ) -> tuple[int, int, Point]:
        while max_size != 1:

            ttf_font = ImageFont.truetype(self.fontset.default, size=max_size, encoding="utf-8")
            bbox = ttf_font.getbbox("|`A")
            new_line_height = int(abs(bbox[3] - bbox[1])) + 5
            current_max_size = Point(0, new_line_height)
            current_position = Point(0, 0)

            for entity in enitites:
                if entity["type"] in (
                    "default",
                    "bold",
                    "italic",
                    "code",
                    "code_block",
                    "qoute",
                    "underline",
                    "link",
                ):
                    ttf_font = ImageFont.truetype(
                        entity.get("font", self.fontset.default),
                        size=max_size,
                        encoding="utf-8",
                    )
                    emoji_len = len(
                        list(
                            filter(
                                lambda x: x["type"] == "emoji",
                                self.chunk_by_emoji(entity.get("content", "")),
                            )
                        )
                    )
                    box_x = math.ceil(
                        ttf_font.getlength(entity.get("content", ""))
                        + (emoji_len * new_line_height) / self.emoji_scale
                    )
                    if entity["type"] == "code_block":
                        box_x += 5
                    current_position = Point(current_position.x + box_x, current_position.y)

                    current_max_size = Point(
                        max(current_max_size.x, current_position.x),
                        max(current_max_size.y, current_position.y + new_line_height),
                    )

                elif entity["type"] == "new_line":
                    current_position = Point(0, current_position.y + new_line_height)
                    current_max_size = Point(
                        max(current_max_size.x, current_position.x),
                        max(current_max_size.y, current_position.y + new_line_height),
                    )
                elif entity["type"] == "emoji":
                    current_position = Point(
                        current_max_size.x + math.ceil(new_line_height * self.emoji_scale),
                        current_max_size.y,
                    )
                    current_max_size = Point(
                        max(current_max_size.x, current_position.x),
                        max(current_max_size.y, current_position.y + new_line_height),
                    )
                else:
                    typing.assert_never(entity["type"])

            if (
                current_max_size.x < max_box_size.width
                and (current_max_size.y + new_line_height) < max_box_size.height
            ):
                return (
                    max_size,
                    new_line_height,
                    Point(
                        int(current_max_size.x),
                        int(current_max_size.y + new_line_height),
                    ),
                )
            max_size -= 1
        return max_size, 1, Point(1, 1)

    def chunk_by_emoji(self, text: str) -> list[dict]:
        chunked_text = []
        for chunk in self.emoji_regex.split(text):
            if not chunk:
                continue

            if chunk in self.emoji_table:
                chunked_text.append({"content": chunk, "type": "emoji"})
            else:
                chunked_text.append({"content": chunk, "type": "text"})
        return chunked_text

    def get_content_layer(self, enitites: list[DrawEntity]) -> Image.Image:
        content_layer = Image.new("RGBA", self.base_image.size, color=(0, 0, 0, 0))
        self._dbg_draw_bbox(
            content_layer,
            self.grid.content_box,
            title="content-box " + str(self.grid.content_box.to_point_box()),
            fill=(255, 255, 0, 75),
        )

        current_position = Point(self.grid.content_box.x, self.grid.content_box.y)
        draw = ImageDraw.Draw(content_layer)

        font_size, new_line_size, _ = self.get_entities_fontsize(
            enitites, max_size=128, max_box_size=self.grid.content_box.size
        )

        for entity in enitites:
            if entity["type"] in (
                "default",
                "bold",
                "italic",
                "code",
                "link",
            ):

                content = entity.get("content", "")
                self._dbg_draw_anchor(
                    content_layer,
                    current_position,
                    size=Point(50, 50),
                    fill=(200, 0, 0, 100),
                )
                draw_symbols: list[str | Image.Image] = []

                for chunk in self.emoji_regex.split(content):
                    if not chunk:
                        continue

                    if chunk in self.emoji_table:
                        draw_symbols.append(
                            Image.open(io.BytesIO(self.emoji_table[chunk].read_bytes())).convert(
                                "RGBA"
                            )
                        )
                    else:
                        draw_symbols.append(chunk)

                font = ImageFont.truetype(
                    entity.get("font", self.fontset.default),
                    size=font_size,
                )

                for chunk in self.chunk_by_emoji(content):
                    if chunk["type"] == "emoji":
                        emoji_size = math.floor(new_line_size / self.emoji_scale)
                        emoji_image = Image.open(self.emoji_table[chunk["content"]]).resize(
                            (emoji_size, emoji_size),
                            resample=Image.Resampling.LANCZOS,
                        )
                        content_layer.paste(emoji_image, current_position, mask=emoji_image)
                        current_position = Point(
                            current_position.x + emoji_size, current_position.y
                        )
                    else:
                        length = font.getlength(chunk["content"])
                        draw.text(
                            current_position,
                            chunk["content"],
                            font=font,
                            fill=entity.get("color", self.colorset.content),
                            anchor="lt",
                        )
                        current_position = Point(
                            current_position.x + int(length), current_position.y
                        )

            elif entity["type"] == "new_line":
                current_position = Point(
                    self.grid.content_box.x, current_position.y + new_line_size
                )
            elif entity["type"] == "emoji":
                emoji_size = math.floor(new_line_size / self.emoji_scale)
                emoji_image = Image.open(entity["emoji_image"]).resize(  # type: ignore
                    (emoji_size, emoji_size),
                    resample=Image.Resampling.LANCZOS,
                )
                content_layer.paste(emoji_image, current_position, mask=emoji_image)
                current_position = Point(current_position.x + new_line_size, current_position.y)
            else:
                typing.assert_never(entity["type"])

        return content_layer

    def get_diviner_layer(self) -> Image.Image:
        diviner_layer = Image.new("RGBA", self.base_image.size, color=(0, 0, 0, 0))
        self._dbg_draw_bbox(
            diviner_layer,
            self.grid.diviner_box,
            title="diviner-box " + str(self.grid.diviner_box.to_point_box()),
            fill=(0, 0, 255, 75),
        )
        return diviner_layer

    def get_author_image_layer(self, author_image: bytes) -> Image.Image:
        diviner_layer = Image.new("RGBA", self.base_image.size, color=(0, 0, 0, 0))
        self._dbg_draw_bbox(
            diviner_layer,
            self.grid.author_image_box,
            title="author-image-box " + str(self.grid.author_image_box.to_point_box()),
            fill=(255, 0, 255, 75),
        )

        ai = Image.open(io.BytesIO(author_image)).resize(
            self.grid.author_image_box.size, resample=Image.Resampling.LANCZOS
        )

        if self.author_image_type == "circle":
            mask = Image.new("L", ai.size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, *ai.size), fill=255)
        elif self.author_image_type == "square":
            mask = Image.new("L", ai.size, 255)
        elif self.author_image_type == "rounded":
            mask = Image.new("L", ai.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, *ai.size), 30, outline=255, fill=255)
        else:
            typing.assert_never(self.author_image_type)

        ai.putalpha(mask)
        diviner_layer.paste(
            ai,
            box=self.grid.author_image_box.to_point_box(),
            mask=ai,
        )

        return diviner_layer

    def get_author_name_layer(self, author_name: str) -> Image.Image:
        diviner_layer = Image.new("RGBA", self.base_image.size, color=(0, 0, 0, 0))
        self._dbg_draw_bbox(
            diviner_layer,
            self.grid.author_name_box,
            title="author-name-box " + str(self.grid.author_name_box.to_point_box()),
            fill=(0, 255, 255, 75),
        )

        draw = ImageDraw.Draw(diviner_layer)

        font_size, text_size = self.text_processor.get_line_size_by_box(
            author_name,
            self.grid.author_name_box.size,
            font_path=self.fontset.bold,
        )
        position = Point(
            self.grid.author_name_box.x,
            self.grid.author_name_box.y + self.grid.author_name_box.height // 2,
        )

        self.text_processor.draw_single_line(
            draw,
            position,
            TextDrawEntity(
                type="bold",
                offset=0,
                length=len(author_name),
                content=author_name,
                font=self.fontset.bold,
                color=self.colorset.author_name,
            ),
            font_size=font_size,
            emoji_size=math.floor(text_size.height * self.emoji_scale),
        )
        self._dbg_draw_anchor(
            diviner_layer,
            position,
            Point(200, 200),
            fill=(255, 0, 0, 75),
            title=f"author-name-anchor {position}",
        )
        self._dbg_draw_bbox(
            diviner_layer,
            self.grid.author_name_box,
            title="author-name-box " + str(self.grid.author_name_box.to_point_box()),
            fill=(0, 0, 255, 75),
        )
        return diviner_layer

    def generate_quote(
        self,
        title: str,
        text: str,
        author_name: str,
        author_image: bytes,
        enitites: list[InputEntity],
    ) -> bytes:

        title_layer = self.get_title_layer(title)
        bi = self.base_image.copy()
        if self.debug:
            self._dbg_draw_grid(bi)
        bi.paste(
            title_layer,
            box=(0, 0),
            mask=title_layer,
        )

        diviner_layer = self.get_diviner_layer()
        bi.paste(
            diviner_layer,
            box=(0, 0),
            mask=diviner_layer,
        )

        draw_entities = self.get_draw_entities(text, enitites)
        content_layer = self.get_content_layer(draw_entities)
        bi.paste(
            content_layer,
            box=(0, 0),
            mask=content_layer,
        )

        author_image_layer = self.get_author_image_layer(author_image)
        bi.paste(
            author_image_layer,
            box=(0, 0),
            mask=author_image_layer,
        )

        author_name_layer = self.get_author_name_layer(author_name)
        bi.paste(
            author_name_layer,
            box=(0, 0),
            mask=author_name_layer,
        )

        if self.debug:
            bi.show()

        _io = io.BytesIO()
        bi.save(_io, format="PNG")
        _io.seek(0)
        return _io.read()

    def _dbg_draw_anchor(
        self,
        image: Image.Image,
        position: Point,
        size: Point,
        fill=None,
        style: typing.Literal["normal", "dashed"] = "normal",
        title: str | None = None,
    ) -> None:
        if not self.debug:
            return
        draw = ImageDraw.Draw(image)
        x_offset = size.x // 2
        y_offset = size.y // 2

        print_fn = (
            draw.line
            if style == "normal"
            else functools.partial(draw_line_dashed, image=image, dashlen=2, ratio=5)
        )
        print_fn(
            xy=(position.x - x_offset, position.y, position.x + x_offset, position.y),
            fill=fill,
        )
        print_fn(
            xy=(position.x, position.y - y_offset, position.x, position.y + y_offset),
            fill=fill,
        )
        if title:
            draw.text(
                (position.x + 5, position.y + 5),
                title,
                font=ImageFont.truetype(self.fontset.default, size=12),
                fill=fill,
            )

    def _dbg_draw_bbox(
        self, image: Image.Image, box: SizeBox, title: str | None = None, fill=None
    ) -> None:
        if not self.debug:
            return
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            box.to_point_box(),
            outline=fill,
        )

        if title:
            draw.text(
                (box.x + 5, box.y + 5),
                title,
                font=ImageFont.truetype(self.fontset.default, size=12),
                fill=fill,
            )

    def _dbg_draw_grid(self, image: Image.Image) -> None:
        if not self.debug:
            return
        for xi in range(0, image.size[0] + 1, 100):
            for yi in range(0, image.size[1] + 1, 100):
                self._dbg_draw_anchor(
                    image,
                    Point(xi, yi),
                    Point(image.size[0], image.size[1]),
                    (0, 255, 0, 10),
                    style="dashed",
                )
