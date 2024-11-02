import abc
import functools
import pathlib
import re
import typing

from PIL import Image


class ChunkResult(typing.TypedDict):
    type: typing.Literal["emoji", "text"]
    content: str


class ABCEmojiSource(abc.ABC):

    @abc.abstractmethod
    def get_image(self, emoji_id: str) -> Image.Image: ...
    @abc.abstractmethod
    def is_emoji(self, emoji_id: str) -> bool: ...
    @abc.abstractmethod
    def get_emoji_regex(self) -> re.Pattern: ...

    def chunk_by_emoji(self, text: str) -> list[ChunkResult]:
        chunks = []
        for chunk in self.get_emoji_regex().split(text):
            if not chunk:
                continue
            if self.is_emoji(chunk):
                chunks.append(ChunkResult(type="emoji", content=chunk))
                continue
            chunks.append(ChunkResult(type="text", content=chunk))
        return chunks

    def get_emoji_count(self, text: str) -> int:
        return len(
            list(filter(lambda x: x["type"] == "emoji", self.chunk_by_emoji(text)))
        )

    def get_emojies(self, text: str) -> list[str]:
        return [
            it["content"] for it in self.chunk_by_emoji(text) if it["type"] == "emoji"
        ]


class FileEmojiSource(ABCEmojiSource):

    def __init__(self, emoji_dir: pathlib.Path = pathlib.Path("emoji")):
        self.emoji_dir = emoji_dir

    @functools.cached_property
    def emoji_table(self) -> dict[str, pathlib.Path]:
        return {
            "".join(
                chr(int(code, 16)) for code in it.stem.replace("U+", "").split()
            ): it
            for it in self.emoji_dir.glob("*.png")
        }

    @functools.cache  # noqa: B019
    def get_emoji_regex(self) -> re.Pattern:  # type: ignore
        emoji_patterns = sorted(self.emoji_table.keys(), key=len, reverse=True)
        regex_pattern = "|".join(map(re.escape, emoji_patterns))
        return re.compile(f"({regex_pattern})")

    def is_emoji(self, emoji_id: str) -> bool:
        return emoji_id in self.emoji_table

    def get_image(self, emoji_id: str) -> Image.Image:
        return Image.open(self.emoji_table[emoji_id]).convert("RGBA")
