import abc
import typing

from PIL import Image

if typing.TYPE_CHECKING:
    from QIG.generator import QuoteGenerator


class BaseLayer(abc.ABC):

    def __init__(self, generator: "QuoteGenerator") -> None:
        self.generator = generator

    @abc.abstractmethod
    def pipe(self, im: Image.Image, generator: "QuoteGenerator", /, **kwargs) -> None: ...


