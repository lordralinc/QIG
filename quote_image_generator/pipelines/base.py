import abc
import typing

from PIL import Image

if typing.TYPE_CHECKING:
    from quote_image_generator.generator import QuoteGenerator

__all__ = (
    "BasePipeLine",
    "RedirectKeywordPipeLine",
)


class BasePipeLine(abc.ABC):

    def __init__(self, **kwargs) -> None:
        self.pipe_kwargs = kwargs

    @abc.abstractmethod
    def pipe(
        self, im: Image.Image, generator: "QuoteGenerator", /, **kwargs
    ) -> typing.Optional[dict[str, typing.Any]]: ...


class RedirectKeywordPipeLine(BasePipeLine, abc.ABC):
    """
    RedirectKeywordPipeLine is an abstract pipeline class that dynamically redirects
    specific keyword arguments based on a given prefix. It is designed to manage
    complex sets of parameters by categorizing them under a unique key, simplifying
    how arguments are passed and used within the pipeline.

    Parameters:
    - `key` (str): The unique identifier prefix for this pipeline's arguments, used to filter
      and redirect relevant parameters.
    - `required_keys` (Optional[list[str]]): List of required argument names prefixed by `key`.
      Defaults to an empty list if not provided, but subclasses may specify `REQUIRED_ARGS`
      to set their required fields.
    - `optional_keys` (Optional[list[str]]): List of optional argument names prefixed by `key`.
      Defaults to an empty list if not provided, but subclasses may specify `OPTIONAL_ARGS`
      to set their optional fields.

    Methods:
    - `pipe`: Primary method that applies transformations to the image and utilizes redirected
      arguments. Calls an abstract `_pipe` method for the specific implementation of
      transformations.
    - `_get_kwargs`: Internal helper that gathers required and optional arguments prefixed
      by the given `key`, allowing flexible keyword handling.

    Abstract Methods:
    - `_pipe`: Subclasses must implement this method to define their specific behavior
      when the pipeline is executed.
    """

    def __init__(
        self,
        key: str,
        required_keys: typing.Optional[list[str]] = None,
        optional_keys: typing.Optional[list[str]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
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
    ) -> typing.Optional[dict[str, typing.Any]]: ...

    def pipe(
        self, im: Image.Image, generator: "QuoteGenerator", /, **kwargs
    ) -> typing.Optional[dict[str, typing.Any]]:
        return self._pipe(
            im,
            generator,
            **self._get_kwargs(**kwargs),
        )
