import base64
import pathlib

import requests
from bs4 import BeautifulSoup
from rich.progress import (
    FileSizeColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)

file = pathlib.Path("content.html")

url = "https://unicode.org/emoji/charts/full-emoji-list.html"


def download_file(url: str, filepath: pathlib.Path) -> pathlib.Path:

    curr_len = 8192
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        FileSizeColumn(),
        TransferSpeedColumn(),
        TimeElapsedColumn(),
    ) as progress, requests.get(url, stream=True) as r:
        task = progress.add_task("Downloading")
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                curr_len += 8192
                progress.update(task, total=curr_len, advance=len(chunk))
                f.write(chunk)
    return filepath


if file.exists():
    content = file.read_text()
else:
    download_file(url, file)
    content = file.read_text()

soup = BeautifulSoup(content, features="html.parser")


for tr in soup.find_all("tr"):
    emoji_code = tr.find("td", {"class": "code"})
    if not emoji_code:
        continue
    emoji_code_txt = emoji_code.text
    emoji_data = tr.find("td", {"class": "andr alt"}) or tr.find(
        "td", {"class": "andr"}
    )
    if not emoji_data:
        continue

    for child in emoji_data.children:
        if child.name == "img":
            emoji_data_txt = child.attrs["src"]
            pathlib.Path("emoji", emoji_code_txt + ".png").write_bytes(
                base64.b64decode(emoji_data_txt.replace("data:image/png;base64,", ""))
            )
