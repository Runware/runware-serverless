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

ENDPOINT_PATH_PATTERN = r"^[a-z]([a-z0-9-]{0,62}[a-z0-9])?(/[a-z]([a-z0-9-]{0,62}[a-z0-9])?)*$"
"""One or more lowercase segments joined by slashes, each up to 64."""

MAX_ENDPOINT_PATH_LENGTH = 255
"""The whole path, which the pattern bounds per segment and not in total."""

ENDPOINT_PATH_ATTRIBUTE = "__runware_endpoint_path__"
"""Where ``endpoint`` records a method's path.

Public deliberately: it is how the builder discovers declared endpoints, so the
name is part of the contract rather than an implementation detail.
"""

ENDPOINT_DEFAULT_ATTRIBUTE = "__runware_endpoint_default__"
"""Where ``endpoint`` records that a method is the app's default.

Public for the same reason, and absent rather than ``False`` on every other
handler: the build reads the attribute to decide which endpoint a root
invocation reaches.
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
            f"@endpoint decorates a method, got {given!r}. A path is the path "
            "keyword: @endpoint(path='v1/chat/completions')."
        )


class EndpointNameError(ValueError):
    """A method name does not derive a legal endpoint path."""

    def __init__(self, name: str, path: str) -> None:
        super().__init__(
            f"{name} would serve the path {path!r}, which is not legal. A path "
            "is one or more lowercase segments joined by slashes, each starting "
            "with a letter and holding letters digits and hyphens, up to 64 "
            f"characters per segment and {MAX_ENDPOINT_PATH_LENGTH} in all."
        )


class DuplicateEndpointError(ValueError):
    """Two methods claim one endpoint path."""

    def __init__(self, path: str, first: str, second: str) -> None:
        super().__init__(
            f"duplicate endpoint path {path!r}: claimed by both {first!r} and {second!r}"
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


@overload
def endpoint(handler: _HandlerT) -> _HandlerT: ...


@overload
def endpoint(
    handler: None = None,
    *,
    path: str | None = None,
    default: bool = False,
) -> Callable[[_HandlerT], _HandlerT]: ...


def endpoint(
    handler: _HandlerT | None = None,
    *,
    path: str | None = None,
    default: bool = False,
) -> _HandlerT | Callable[[_HandlerT], _HandlerT]:
    """Mark a method as callable.

    Bare, the path is the method name with each underscore turned into a
    hyphen, so ``run_upscale`` serves ``run-upscale``. ``path`` names a route
    the method name cannot spell, ``v1/chat/completions`` among them, and
    ``default`` marks the endpoint a root invocation reaches, which an app
    marks once at most. The handler comes back unwrapped either way, so its
    signature, annotations and defaults stay exactly as written, for the
    platform's schema introspection and for a type checker.

    ``@endpoint("run-upscale")`` is refused: a path is the ``path`` keyword,
    and the positional form is the mistake a reader of another framework's
    decorator arrives with. The type variable is bound to ``Callable``, so that
    spelling is a type error at the decoration site as well as a ``TypeError``
    at import.
    """

    def decorate(method: _HandlerT) -> _HandlerT:
        resolved = path if path is not None else method.__name__.replace("_", "-")
        if (
            len(resolved) > MAX_ENDPOINT_PATH_LENGTH
            or _endpoint_path_pattern.fullmatch(resolved) is None
        ):
            raise EndpointNameError(method.__name__, resolved)
        setattr(method, ENDPOINT_PATH_ATTRIBUTE, resolved)
        if default:
            setattr(method, ENDPOINT_DEFAULT_ATTRIBUTE, True)
        return method

    if handler is not None:
        if not callable(handler):
            raise EndpointArgumentError(handler)
        return decorate(handler)
    return decorate


def endpoints(model_class: type) -> dict[str, Callable[..., Any]]:
    """The handlers ``model_class`` declares, keyed by path.

    Scans the whole MRO, so a class built on a shared base serves the base's
    endpoints too, and each path resolves through ``model_class`` so an override
    serves its own implementation whether or not it decorates it again. A
    subclass that decorates the inherited name again replaces the inherited
    path rather than adding a second one.

    Two different method names that claim one path raise rather than letting
    the later one win: an explicit ``path`` makes that collision easy to write,
    and a registry that resolved it silently would pass a customer's own tests
    and then fail their build.

    A class that decorates nothing falls back to ``predict`` at the default
    path. A class with neither raises.
    """
    declared: dict[str, Callable[..., Any]] = {}
    claimed_by: dict[str, str] = {}
    stamped: set[str] = set()
    for klass in model_class.__mro__:
        for name, member in vars(klass).items():
            if name in stamped:
                continue
            path = getattr(member, ENDPOINT_PATH_ATTRIBUTE, None)
            if path is None or not callable(member):
                continue
            stamped.add(name)
            owner = claimed_by.setdefault(path, name)
            if owner != name:
                raise DuplicateEndpointError(path, owner, name)
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
