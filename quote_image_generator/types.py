import typing

import typing_extensions

__all__ = (
    "Point",
    "Size",
    "SizeBox",
    "PointBox",
    "FontSet",
    "Color",
    "ColorSet",
    "InputEntityType",
    "InputEntity",
    "EmojiDrawEntity",
    "NewLineDrawEntity",
    "TextDrawEntityTypes",
    "TextDrawEntity",
    "DrawEntity",
    "type_cast",
)


class Point(typing.NamedTuple):
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"


class Size(typing.NamedTuple):
    width: int
    height: int

    def __str__(self) -> str:
        return f"({self.width}, {self.height})"


class SizeBox(typing.NamedTuple):
    x: int
    y: int
    width: int
    height: int

    def to_point_box(self) -> "PointBox":
        return PointBox(self.x, self.y, self.x + self.width, self.y + self.height)

    @property
    def size(self) -> Size:
        return Size(self.width, self.height)

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, w={self.width}, h={self.height})"


class PointBox(typing.NamedTuple):
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def size(self) -> Size:
        return Size(abs(self.x1 - self.x0), abs(self.y1 - self.y0))

    def to_size_box(self) -> "SizeBox":
        return SizeBox(self.x0, self.y0, *self.size)

    def __str__(self) -> str:
        return f"({self.x0}, {self.y0}) ({self.x1}, {self.y1})"


class FontSet(typing.NamedTuple):
    default: str
    bold: str
    italic: str
    mono: str


Color: typing_extensions.TypeAlias = typing.Union[
    str, tuple[int, int, int], tuple[int, int, int, int]
]


class ColorSet(typing.NamedTuple):
    default: Color
    link: Color
    code: Color


InputEntityType = typing.Literal[
    "link",
    "bold",
    "italic",
    "underline",
    "strikethrough",
    "code",
    "code_block",
    "quote",
    "emoji",
]


class InputEntity(typing.TypedDict):
    type: InputEntityType
    offset: int
    length: int
    emoji_image: typing_extensions.NotRequired[bytes]


class EmojiDrawEntity(typing.TypedDict):
    type: typing.Literal["emoji"]
    offset: int
    length: int
    emoji_image: bytes


class NewLineDrawEntity(typing.TypedDict):
    type: typing.Literal["new_line"]
    offset: int
    length: int


TextDrawEntityTypes = typing.Literal[
    "default",
    "link",
    "bold",
    "italic",
    "underline",
    "strikethrough",
    "code",
    "code_block",
    "quote",
    "emoji",
]


class TextDrawEntity(typing.TypedDict):
    type: TextDrawEntityTypes
    offset: int
    length: int
    content: str
    font: str
    color: Color


DrawEntity: typing_extensions.TypeAlias = typing.Union[
    EmojiDrawEntity, NewLineDrawEntity, TextDrawEntity
]


T = typing.TypeVar("T")


def type_cast(
    value: typing.Any,
    expected_type: type[T],  # noqa: ARG001
) -> T:
    return value
