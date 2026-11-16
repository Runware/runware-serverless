"""The surface a customer writes an app against.

Two decorators and a block, no dependencies beyond the standard library. Neither
decorator changes what it decorates: they record, and hand the class or the
method back exactly as written, so the file stays importable and testable on the
author's machine. The platform reads what they recorded when it imports the model
file, in the build pod and again in the worker.

``imports`` is where a model file holds the imports that only resolve where it
runs. Here it runs its body and suppresses nothing; the build suppresses, in the
platform's own copy of this surface (``_imports``).

Nothing else is re-exported. The error classes and the readers live in
``runware_serverless._endpoints`` and are not part of the published surface. It
is three names on purpose: each one is a compatibility promise for as long as
this distribution lives.
"""

from runware_serverless._endpoints import endpoint, serve
from runware_serverless._imports import imports

__all__ = ["endpoint", "imports", "serve"]
