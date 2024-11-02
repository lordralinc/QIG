import pathlib

from PIL import Image

from QIG.generator import QuoteGenerator
from QIG.types import ColorSet, FontSet, Grid, SizeBox

generator = QuoteGenerator(
    bi=Image.new("RGBA", (1600, 900), color=(0, 0, 0)),
    fontset=FontSet(
        "roboto/Roboto-Regular.ttf",
        "roboto/Roboto-Bold.ttf",
        "roboto/Roboto-Italic.ttf",
        "roboto/Roboto-Mono.ttf",
    ),
    grid=Grid(
        title_box=SizeBox(x=50, y=15, width=1500, height=50),
        diviner_box=SizeBox(x=50, y=75, width=1500, height=100),
        content_box=SizeBox(x=50, y=175, width=1500, height=900 - 200 - 175 - 15 - 15),
        author_image_box=SizeBox(x=50, y=900 - 200 - 15, width=200, height=200),
        author_name_box=SizeBox(
            x=275, y=900 - 200 - 15 + 75, width=1600 - 50 - 275, height=50
        ),
    ),
    colorset=ColorSet(
        title=(255, 255, 255),
        content=(255, 255, 255),
        link=(0, 0, 255),
        code=(255, 0, 0),
        author_name=(255, 255, 255),
    ),
    author_image_type="rounded",
    emoji_scale=1,
    debug=True,
)


output = generator.generate_quote(
    "Цитаты великих людей ❤️‍🔥❤️‍🔥❤️‍🔥",
    "ЫЫЫЫЫЫЫЫыыыыы 😂👍\n\nЫЫывыыыыыыы 😂👍\n❤️‍🔥",
    "© Юрий Юшманов ❤️‍🔥❤️‍🔥❤️‍🔥",
    pathlib.Path("avatar.jpg").read_bytes(),
    [],
)
