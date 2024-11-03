import io
import typing

import typing_extensions
from PIL import Image, ImageDraw

from quote_image_generator.generator import QuoteGenerator
from quote_image_generator.pipelines.base import RedirectKeywordPipeLine
from quote_image_generator.types import SizeBox

__all__ = ("ImagePipeLine", "CircleImagePipeLine", "RoundedImagePipeLine")


class ImagePipeLine(RedirectKeywordPipeLine):
    REQUIRED_ARGS: typing.ClassVar[list[str]] = [
        "box",
        "image",
    ]

    def get_mask(self, image: Image.Image) -> Image.Image:
        return Image.new("L", image.size, 255)

    def _pipe(
        self,
        im: Image.Image,
        generator: QuoteGenerator,
        *,
        box: SizeBox,
        image: typing.Union[bytes, Image.Image],
        **kwargs,
    ) -> None:
        image = (
            image
            if isinstance(image, Image.Image)
            else Image.open(
                io.BytesIO(image),
            )
            .convert("RGBA")
            .resize(box.size, resample=Image.Resampling.LANCZOS)
        )
        image.putalpha(self.get_mask(image))
        im.paste(image, (box.x, box.y), mask=image)


class CircleImagePipeLine(ImagePipeLine):

    @typing_extensions.override
    def get_mask(self, image: Image.Image) -> Image.Image:
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, *image.size), fill=255)
        return mask


class RoundedImagePipeLine(ImagePipeLine):

    @typing_extensions.override
    def get_mask(self, image: Image.Image) -> Image.Image:
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, *image.size),
            30,
            outline=255,
            fill=255,
        )
        return mask
