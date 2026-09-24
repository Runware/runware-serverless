"""The marks the decorators leave, and the readers the platform uses.

Everything here is standard library. The platform's own package reads these
attributes off the imported class; it does not need this module at runtime, and
this module never imports it.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar, overload

DEFAULT_ENDPOINT_PATH = "predict"
"""Path a class serves when it decorates nothing and defines ``predict``."""

ENDPOINT_PATH_PATTERN = r"^[a-z]([a-z0-9-]{0,62}[a-z0-9])?$"
"""Lowercase, starts with a letter, letters digits and hyphens, up to 64."""

ENDPOINT_PATH_ATTRIBUTE = "__runware_endpoint_path__"
"""Where ``endpoint`` records a method's path.

Public deliberately: it is how the builder discovers declared endpoints, so the
name is part of the contract rather than an implementation detail.
"""

SERVE_OPTIONS_ATTRIBUTE = "__runware_serve_options__"
"""Where ``serve`` records the options it was called with."""

_HandlerT = TypeVar("_HandlerT", bound=Callable[..., Any])
_ModelT = TypeVar("_ModelT", bound=type)

_endpoint_path_pattern = re.compile(ENDPOINT_PATH_PATTERN)


class EndpointArgumentError(TypeError):
    """``endpoint`` was given something other than a method."""

    def __init__(self, given: object) -> None:
        super().__init__(
            f"@endpoint takes no arguments and decorates a method, got {given!r}. "
            "The path is the method name with underscores turned into hyphens."
        )


class EndpointNameError(ValueError):
    """A method name does not derive a legal endpoint path."""

    def __init__(self, name: str, path: str) -> None:
        super().__init__(
            f"{name} derives the path {path!r}, which is not legal. A path is "
            "lowercase, starts with a letter, holds letters digits and hyphens, "
            "and is at most 64 characters."
        )


class NoEndpointsError(TypeError):
    """A served class declares nothing to call."""

    def __init__(self, name: str) -> None:
        super().__init__(
            f"{name} has no endpoints. Mark a method with @endpoint, or define "
            f"{DEFAULT_ENDPOINT_PATH}."
        )


@dataclass(frozen=True)
class ServeOptions:
    """What ``serve`` was called with, recorded for the platform to read."""

    encode_response: Callable[[list[Any]], Any] | None = None


def endpoint(handler: _HandlerT) -> _HandlerT:
    """Mark a method as callable at the path its name derives.

    ``run_upscale`` serves ``run-upscale``. The handler comes back unwrapped, so
    its signature, annotations and defaults stay exactly as written, for the
    platform's schema introspection and for a type checker.

    ``@endpoint("run-upscale")`` is rejected by name rather than reaching the
    method: the path is not configurable, and the argument form is the mistake a
    reader of another framework's decorator arrives with. The type variable is
    bound to ``Callable``, so that spelling is a type error at the decoration
    site as well as a ``TypeError`` at import.
    """
    if not callable(handler):
        raise EndpointArgumentError(handler)
    path = handler.__name__.replace("_", "-")
    if _endpoint_path_pattern.fullmatch(path) is None:
        raise EndpointNameError(handler.__name__, path)
    setattr(handler, ENDPOINT_PATH_ATTRIBUTE, path)
    return handler


def endpoints(model_class: type) -> dict[str, Callable[..., Any]]:
    """The handlers ``model_class`` declares, keyed by path.

    Scans the whole MRO, so a class built on a shared base serves the base's
    endpoints too, and each path resolves through ``model_class`` so an override
    serves its own implementation whether or not it decorates it again.

    A class that decorates nothing falls back to ``predict`` at the default
    path. A class with neither raises.
    """
    declared: dict[str, Callable[..., Any]] = {}
    for klass in reversed(model_class.__mro__):
        for name, member in vars(klass).items():
            path = getattr(member, ENDPOINT_PATH_ATTRIBUTE, None)
            if path is None or not callable(member):
                continue
            declared[path] = getattr(model_class, name)
    if declared:
        return declared
    fallback = getattr(model_class, DEFAULT_ENDPOINT_PATH, None)
    if callable(fallback):
        return {DEFAULT_ENDPOINT_PATH: fallback}
    raise NoEndpointsError(model_class.__name__)


@overload
def serve(model_class: _ModelT) -> _ModelT: ...


@overload
def serve(
    *,
    encode_response: Callable[[list[Any]], Any] | None = ...,
) -> Callable[[_ModelT], _ModelT]: ...


def serve(
    # Any, because the two overloads above are the contract this signature only
    # has to be wide enough to implement.
    model_class: Any = None,
    *,
    encode_response: Callable[[list[Any]], Any] | None = None,
) -> Any:
    """Record the class as the app the worker serves.

    Used bare (``@serve``) or called (``@serve(encode_response=...)``). The
    class comes back unchanged and undecorated, so a model file can be imported
    for the class it defines, by the platform or by your own tests, without that
    class having turned into something else.

    Endpoints resolve here rather than at the first request, so a class with
    nothing to serve fails while the file is being imported.
    """
    if model_class is None:

        def decorate(cls: _ModelT) -> _ModelT:
            return _record(cls, encode_response=encode_response)

        return decorate
    return _record(model_class, encode_response=encode_response)


def serve_options(model_class: type) -> ServeOptions:
    """The options ``serve`` recorded for ``model_class``.

    Raises for a class that was never decorated, which is the mistake worth
    naming: the alternative is an AttributeError from somewhere further in.
    """
    options = model_class.__dict__.get(SERVE_OPTIONS_ATTRIBUTE)
    if options is None:
        detail = f"{model_class.__name__} is not decorated with @serve"
        raise TypeError(detail)
    return options


def _record(
    model_class: _ModelT,
    *,
    encode_response: Callable[[list[Any]], Any] | None,
) -> _ModelT:
    endpoints(model_class)
    setattr(
        model_class,
        SERVE_OPTIONS_ATTRIBUTE,
        ServeOptions(encode_response=encode_response),
    )
    return model_class
