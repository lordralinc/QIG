import abc
import functools
import logging
import pathlib
import re
import typing

from PIL import Image

logger = logging.getLogger(__name__)


class ChunkResult(typing.TypedDict):
    type: typing.Literal["emoji", "text"]
    content: str


class ABCEmojiSource(abc.ABC):

    def __init__(self, emoji_scale: float = 1.1) -> None:
        self.emoji_scale = emoji_scale

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
        logger.debug(f"Parsed text {text} to {chunks}")
        return chunks

    def get_emoji_count(self, text: str) -> int:
        return len(list(filter(lambda x: x["type"] == "emoji", self.chunk_by_emoji(text))))

    def get_emojies(self, text: str) -> list[str]:
        return [it["content"] for it in self.chunk_by_emoji(text) if it["type"] == "emoji"]


class FileEmojiSource(ABCEmojiSource):

    def __init__(self, emoji_dir: pathlib.Path = pathlib.Path("emoji"), emoji_scale: float = 1.1):
        self.emoji_dir = emoji_dir
        super().__init__(emoji_scale=emoji_scale)

    @functools.cached_property
    def emoji_table(self) -> dict[str, pathlib.Path]:
        logger.debug(f"Load emoji table from {self.emoji_dir}")
        return {
            "".join(chr(int(code, 16)) for code in it.stem.replace("U+", "").split()): it
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

    def download_from_unicode(self) -> None:
        import requests

        url = "https://unicode.org/emoji/charts/full-emoji-list.html"
        output_file = self.emoji_dir / "full-emoji-list.html"
        output_file.unlink(missing_ok=True)

        curr_len = 0

        logger.debug("Downloading full-emoji list from unicode")

        with requests.get(url, stream=True, timeout=60 * 60) as r:
            r.raise_for_status()
            with open(output_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    curr_len += len(chunk)
                    logger.debug(f"Downloading full-emoji list from unicode: {curr_len}")
                    f.write(chunk)

    def parse_from_unicode_html(self) -> None:
        import base64

        from bs4 import BeautifulSoup

        output_file = self.emoji_dir / "full-emoji-list.html"

        logger.debug(f"Parse full-emoji list from {output_file}")

        soup = BeautifulSoup(output_file.read_text(encoding="utf-8"), features="html.parser")
        for tr in soup.find_all("tr"):
            emoji_code = tr.find("td", {"class": "code"})
            if not emoji_code:
                continue
            emoji_code_txt = emoji_code.text
            emoji_data = tr.find("td", {"class": "andr alt"}) or tr.find("td", {"class": "andr"})
            if not emoji_data:
                continue

            for child in emoji_data.children:
                if child.name == "img":
                    emoji_data_txt = child.attrs["src"]
                    outfile = pathlib.Path("emoji", emoji_code_txt + ".png")
                    outfile.write_bytes(
                        base64.b64decode(emoji_data_txt.replace("data:image/png;base64,", ""))
                    )
                    logger.debug(f"Downloaded emoji {emoji_code_txt} to {outfile}")
