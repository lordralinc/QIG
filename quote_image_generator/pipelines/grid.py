import typing

from PIL import Image

from quote_image_generator.pipelines.base import BasePipeLine
from quote_image_generator.types import SizeBox

if typing.TYPE_CHECKING:
    from quote_image_generator.generator import QuoteGenerator

__all__ = ("GridResizePipeLine",)


class GridResizePipeLine(BasePipeLine):
    """
    `GridResizePipeLine` is a pipeline class designed to adjust bounding boxes to fit a new
    image resolution. It scales each box according to the change in resolution, ensuring
    consistent positioning and sizing across different image dimensions. This pipeline is
    particularly useful when images are resized while maintaining layout consistency.

    Methods:
    - `_resize_box`: Internal method that takes a bounding box (`SizeBox`) and scales it based
      on the ratio between the original resolution and the new resolution. Returns a resized
      bounding box adjusted to the new dimensions.

    Parameters:
    - `box_keys` (list[str]): List of keys identifying which boxes in the kwargs to resize.
    - `grid_image_size` (tuple[int, int]): The reference resolution for the boxes. Defaults to (1600, 900).
    - `debug` (bool): When True, enables debugging output (not implemented in this version).

    Returns:
    - `dict[str, SizeBox]`: A dictionary with resized bounding boxes, each adjusted to the
      new resolution of the image.

    Example:
        `resized_boxes` = pipeline.pipe(im, generator, box_keys=["box1", "box2"], grid_image_size=(1600, 900))
    """

    def _resize_box(
        self,
        box: SizeBox,
        original_resolution: tuple[int, int],
        new_resolution: tuple[int, int],
    ) -> SizeBox:
        scale_x = new_resolution[0] / original_resolution[0]
        scale_y = new_resolution[1] / original_resolution[1]
        return SizeBox(
            x=int(box.x * scale_x),
            y=int(box.y * scale_y),
            width=int(box.width * scale_x),
            height=int(box.height * scale_y),
        )

    def pipe(
        self,
        im: Image.Image,
        generator: "QuoteGenerator",
        *,
        box_keys: list[str],
        grid_image_size: tuple[int, int] = (1600, 900),
        debug: bool = False,
        **kwargs,
    ) -> dict[str, typing.Any]:
        return {key: self._resize_box(kwargs[key], grid_image_size, im.size) for key in box_keys}
