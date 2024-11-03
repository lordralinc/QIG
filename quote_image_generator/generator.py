import io
import logging
import typing

from PIL import Image

from quote_image_generator.pipelines.base import BasePipeLine
from quote_image_generator.processors.entities import EntitiesProcessor
from quote_image_generator.processors.text import TextProcessor

__all__ = ("QuoteGenerator",)


logger = logging.getLogger(__name__)


class QuoteGenerator:

    def __init__(
        self,
        bi: typing.Union[bytes, Image.Image, tuple[int, int]],
        pipeline: list[BasePipeLine],
        *,
        text_processor: TextProcessor,
        entities_processor: EntitiesProcessor,
        debug: bool = False,
        **kwargs,
    ) -> None:
        self.base_image = (
            bi
            if isinstance(bi, Image.Image)
            else (
                Image.new("RGBA", bi)
                if isinstance(bi, tuple)
                else Image.open(io.BytesIO(bi)).convert("RGBA")
            )
        )
        self.kwargs = {**kwargs, "debug": debug}
        self.text_processor = text_processor
        self.entities_processor = entities_processor

        self.pipeline = pipeline

    def generate_quote(self, **kwargs) -> bytes:

        pipeline_kwargs = {**kwargs, **self.kwargs}

        quote_image = self.base_image.copy().convert("RGBA")

        for pipe in self.pipeline:
            logger.debug(f"Run pipe: {pipe.__class__.__name__}")
            pipe_result = pipe.pipe(quote_image, self, **pipeline_kwargs, **pipe.pipe_kwargs)
            if pipe_result:
                pipeline_kwargs.update(pipe_result)

        output = io.BytesIO()
        quote_image.save(output, format="PNG")
        return output.getvalue()
