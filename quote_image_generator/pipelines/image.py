import io
import typing

import typing_extensions
from PIL import Image, ImageDraw

from quote_image_generator.generator import QuoteGenerator
from quote_image_generator.pipelines.base import RedirectKeywordPipeLine
from quote_image_generator.types import Size, SizeBox

__all__ = ("ImagePipeLine", "CircleImagePipeLine", "RoundedImagePipeLine")


class ImagePipeLine(RedirectKeywordPipeLine):
    """
    `ImagePipeLine` is a pipeline class for adding an image onto a specified area within an existing
    image, with options for alignment and resizing. It supports precise positioning and optionally
    resizes the image to fit squarely within the defined box area, making it adaptable to varied
    layouts and compositions.

    Class Variables:
    - `REQUIRED_ARGS` (list[str]): Specifies "box" and "image" as required arguments.
    - `OPTIONAL_ARGS` (list[str]): Defines optional arguments including:
        - `keep_square`: Boolean to control whether the image should retain square proportions when resized.

    Methods:
    - `get_mask`: Returns an image mask with full opacity, allowing for transparent overlays if needed.
    - `_pipe`: Core method that resizes the image (if needed), aligns it within the box based on specified
      alignment parameters, and pastes it onto the target image.

    Parameters:
    - `box` (SizeBox): The area in which to place the image.
    - `image` (Union[bytes, Image.Image]): The image to be placed, either as bytes or a preloaded image object.
    - `keep_square` (bool): If True, resizes the image to fit within a square, maintaining aspect ratio. Defaults to True.
    - `vertical_align` (Literal["top", "middle", "bottom"]): Vertical alignment within the box.
    - `horizontal_align` (Literal["left", "middle", "right"]): Horizontal alignment within the box.

    Example:
        ```
        pipeline.pipe(
            im, generator,
            box=target_box,
            image=image_data,
            keep_square=True,
            vertical_align="middle",
            horizontal_align="center"
        )
        ```
    """

    REQUIRED_ARGS: typing.ClassVar[list[str]] = [
        "box",
        "image",
    ]
    OPTIONAL_ARGS: typing.ClassVar[list[str]] = [
        "keep_square",
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
        keep_square: bool = True,
        vertical_align: typing.Literal["top", "middle", "bottom"] = "middle",
        horizontal_align: typing.Literal["left", "middle", "right"] = "middle",
        **kwargs,
    ) -> None:

        if keep_square:
            min_size = min(*box.size)
            size = Size(min_size, min_size)
        else:
            size = box.size

        image = (
            image
            if isinstance(image, Image.Image)
            else Image.open(
                io.BytesIO(image),
            )
            .convert("RGBA")
            .resize(size, resample=Image.Resampling.LANCZOS)
        )
        image.putalpha(self.get_mask(image))

        pos = (box.x, box.y)

        if vertical_align == "middle":
            pos = (
                pos[0],
                pos[1] + (box.height - image.height) // 2,
            )
        if vertical_align == "bottom":
            pos = (
                pos[0],
                pos[1] + box.height - image.height,
            )
        if horizontal_align == "middle":
            pos = (
                pos[0] + (box.width - image.width) // 2,
                pos[1],
            )
        if horizontal_align == "right":
            pos = (
                pos[0] + box.width - image.width,
                pos[1],
            )

        im.paste(image, pos, mask=image)


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
