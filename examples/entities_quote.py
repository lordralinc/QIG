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
        pipelines.GradientBackgroundPipeLine(),
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
)


output = generator.generate_quote(
    background_from_color=(255, 0, 0),
    background_to_color=(0, 0, 255),
    background_direction="t-b",
    title_content="❤️‍🔥 Цитаты великих людей ❤️‍🔥",
    title_box=types.SizeBox(50, 50, 1500, 50),
    quote_input_text=(
        "Этот текст написан стандартным шрифтом\n"
        "Этот текст написан жирным шрифтом\n"
        "Этот текст написан курсивом\n"
        "Этот текст подчеркнут\n"
        "Этот текст зачеркнут\n"
        "import os; os.system('rm -rf /')\n"
        "Это ссылка"
    ),
    quote_input_enitites=[
        types.InputEntity(type="quote", offset=0, length=38),
        types.InputEntity(type="bold", offset=39, length=33),
        types.InputEntity(type="italic", offset=73, length=27),
        types.InputEntity(type="underline", offset=101, length=21),
        types.InputEntity(type="strikethrough", offset=123, length=20),
        types.InputEntity(type="code_block", offset=144, length=32),
        types.InputEntity(type="link", offset=177, length=10),
    ],
    quote_box=types.SizeBox(x=50, y=175, width=1500, height=495),
    author_name_content="© Юрий Юшманов ❤️‍🔥",
    author_name_box=types.SizeBox(x=275, y=760, width=1275, height=50),
    author_name_vertical_align="middle",
    author_name_horizontal_align="left",
    author_image_image=pathlib.Path("avatar.jpg").read_bytes(),
    author_image_box=types.SizeBox(x=50, y=685, width=200, height=200),
)

Image.open(io.BytesIO(output)).save("pics/entities_quote.png")
