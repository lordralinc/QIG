import io
import logging
import pathlib

from PIL import Image

from quote_image_generator import QuoteGenerator, pipelines, processors, types

try:
    from rich.logging import RichHandler

    logging.basicConfig(
        level="NOTSET",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
except ImportError:
    logging.basicConfig(level=logging.DEBUG)

emoji_source = processors.FileEmojiSource(pathlib.Path("emoji"))
if not pathlib.Path("emoji", "full-emoji-list.html").exists():
    emoji_source.download_from_unicode()
    emoji_source.parse_from_unicode_html()

generator = QuoteGenerator(
    bi=(1600, 900),
    pipeline=[
        pipelines.StaticColorBackgroundPipeLine(),
        pipelines.TextPipeLine(key="title"),
        pipelines.EntitiesPipeLine(key="quote"),
        pipelines.CircleImagePipeLine("author_image"),
        pipelines.TextPipeLine(key="author_name"),
    ],
    entities_processor=processors.EntitiesProcessor(
        fontset=types.FontSet(
            "roboto/Roboto-Regular.ttf",
            "roboto/Roboto-Bold.ttf",
            "roboto/Roboto-Italic.ttf",
            "roboto/Roboto-Mono.ttf",
        ),
        colorset=types.ColorSet(
            default=(255, 255, 255),
            link=(0, 0, 255),
            code=(255, 0, 0),
        ),
    ),
    text_processor=processors.TextProcessor(emoji_source=emoji_source),
    debug=False,
)


output = generator.generate_quote(
    background_from_color=(255, 0, 0),
    background_to_color=(0, 0, 255),
    background_color=(0, 0, 0),
    background_direction="lt-rb",
    title_content="❤️‍🔥 Цитаты великих людей ❤️‍🔥",
    title_box=types.SizeBox(50, 50, 1500, 50),
    quote_input_text="Ха - ха - ха 😂👍❤️‍🔥",
    quote_input_enitites=[],
    quote_box=types.SizeBox(x=50, y=175, width=1500, height=495),
    author_name_content="© Юрий Юшманов ❤️‍🔥",
    author_name_box=types.SizeBox(x=275, y=760, width=1275, height=50),
    author_name_vertical_align="middle",
    author_name_horizontal_align="left",
    author_image_image=pathlib.Path("avatar.jpg").read_bytes(),
    author_image_box=types.SizeBox(x=50, y=685, width=200, height=200),
)

Image.open(io.BytesIO(output)).save("pics/base_quote.png")
