import typing

from QIG.types import (
    Color,
    DrawEntity,
    EmojiDrawEntity,
    InputEntity,
    NewLineDrawEntity,
    TextDrawEntity,
    TextDrawEntityTypes,
    type_cast,
)

if typing.TYPE_CHECKING:
    from QIG.generator import QuoteGenerator


__all__ = ("EntitiesProcessor",)


class EntitiesProcessor:

    def __init__(self, generator: "QuoteGenerator") -> None:
        self.generator = generator
        self.font_table = {
            "bold": self.generator.fontset.bold,
            "italic": self.generator.fontset.italic,
            "code": self.generator.fontset.mono,
            "code_block": self.generator.fontset.mono,
            "link": self.generator.fontset.italic,
            "underline": self.generator.fontset.default,
        }

    def _split_new_line_content(self, entity: DrawEntity) -> list[DrawEntity]:
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

    def _get_color_by_entity_type(self, entity_type: TextDrawEntityTypes) -> Color:
        if entity_type in ("code", "code_block"):
            return self.generator.colorset.code
        if entity_type == "link":
            return self.generator.colorset.link
        return self.generator.colorset.content

    def _create_text_entities(self, text: str, entity: InputEntity) -> list[DrawEntity]:
        if entity["type"] == "emoji":
            return []

        content = text[entity["offset"] : entity["offset"] + entity["length"]]
        color = self._get_color_by_entity_type(entity["type"])
        font = self.font_table.get(entity["type"], self.generator.fontset.default)

        text_entity = TextDrawEntity(
            type=entity["type"],
            font=font,
            color=color,
            content=content,
            offset=entity["offset"],
            length=len(content),
        )
        return self._split_new_line_content(text_entity)

    def _create_default_entities(self, text: str, start: int, end: int) -> list[DrawEntity]:
        content = text[start:end]
        default_entity = TextDrawEntity(
            type="default",
            content=content,
            offset=start,
            length=len(content),
            font=self.generator.fontset.default,
            color=self.generator.colorset.content,
        )
        return self._split_new_line_content(default_entity)

    def convert_input_to_draw_entity(
        self, text: str, entities: list[InputEntity]
    ) -> list[DrawEntity]:
        draw_entities = []
        index = 0
        while index < len(text):
            entity_found = False
            for entity in entities:
                if entity["offset"] <= index < entity["offset"] + entity["length"]:
                    entity_found = True
                    if entity["type"] in self.font_table:
                        draw_entities.extend(self._create_text_entities(text, entity))
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
