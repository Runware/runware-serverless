"""Where a model file puts the imports that only exist at serving time.

The platform imports the author's model file during a build with none of the
serving dependencies installed, so a module-level ``import torch`` fails that
build and an author otherwise has to put every serving-time import inside
``load`` or a handler. A ``with imports():`` block is where those imports go
instead.

**This package never suppresses anything.** The block runs its body and lets
whatever it raises out, because every phase this package runs in is the author's
own: their editor, their type checker, their test suite, and the worker that
serves their app. Only the build suppresses, and the build runs the platform's
own copy of this surface inside its own pod, where it sets a flag this package
does not have and does not expose. An author who could set that flag could turn
the suppression on in production, and that is the failure this shape exists to
avoid. Exposing it would also publish a second name for a phase that never
happens here.

So a model file with a block cannot be imported on a machine without the serving
dependencies, and that is correct: it is the author's own ``ImportError``, with
its traceback, at the line that caused it. It is also a change from imports
inside ``load``, which let the file import anywhere, and the reason a test suite
that imports the model file needs those dependencies in its dev group.

``imports()`` returns a class rather than using ``contextlib.contextmanager``
because ``__exit__`` has to be annotated as never suppressing. Annotated
``bool``, the decorator's own type, pyright reads a name the block binds as
possibly unbound and reports every later use of it, leaving the author writing
the ``if TYPE_CHECKING`` import this block exists to remove.

The quotes around an annotation naming a deferred type stay. At build time the
platform suppressed the import, so the name is unbound there, and a class-level
annotation is evaluated when the class body runs. A module with
``from __future__ import annotations`` needs no quotes, because every annotation
in it is already a string.
"""

from __future__ import annotations

import typing
from types import TracebackType


class _DeferredImports:
    """What ``imports()`` gives to ``with``. ``with imports():`` is the surface."""

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> typing.Literal[False]:
        # True of every phase this package runs in, and the annotation an author's
        # type checker needs. The platform's own copy returns True here while it is
        # building. That is the one phase that suppresses.
        return False


def imports() -> _DeferredImports:
    """Hold imports that only resolve where the model runs.

    The body runs and binds its names at module scope, for ``load`` and every
    handler to use. The platform's build suppresses whatever it raises, so
    an annotation naming one of those types is quoted:

        from runware_serverless import endpoint, imports, serve

        with imports():
            from my_model.manager import InferenceManager


        @serve
        class Deployment:
            manager: "InferenceManager | None" = None

            def load(self) -> None:
                self.manager = InferenceManager()

    A statement in the block that is not an import is suppressed at build time
    too, and silently, so the block holds imports and nothing else.
    """
    return _DeferredImports()
