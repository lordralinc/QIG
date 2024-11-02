import abc
import typing

from PIL import Image

if typing.TYPE_CHECKING:
    from quote_image_generator.generator import QuoteGenerator


class BasePipeLine(abc.ABC):

    @abc.abstractmethod
    def pipe(
        self, im: Image.Image, generator: "QuoteGenerator", /, **kwargs
    ) -> None | dict[str, typing.Any]: ...


class RedirectKeywordPipeLine(BasePipeLine, abc.ABC):
    def __init__(
        self,
        key: str,
        required_keys: list[str] | None = None,
        optional_keys: list[str] | None = None,
    ):
        self.key = key
        self.required_keys = required_keys or getattr(self, "REQUIRED_ARGS", [])
        self.optional_keys = optional_keys or getattr(self, "OPTIONAL_ARGS", [])

    def _get_kwargs(self, **kwargs) -> dict[str, typing.Any]:
        return {
            **{key: kwargs[f"{self.key}_{key}"] for key in self.required_keys},
            **{
                key: kwargs.get(f"{self.key}_{key}")
                for key in self.optional_keys
                if kwargs.get(f"{self.key}_{key}") is not None
            },
            **kwargs,
        }

    @abc.abstractmethod
    def _pipe(
        self, im: Image.Image, generator: "QuoteGenerator", /, **kwargs
    ) -> None | dict[str, typing.Any]: ...

    def pipe(
        self, im: Image.Image, generator: "QuoteGenerator", /, **kwargs
    ) -> None | dict[str, typing.Any]:
        return self._pipe(
            im,
            generator,
            **self._get_kwargs(**kwargs),
        )
