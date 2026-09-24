"""The surface a customer writes an app against.

Two decorators, no dependencies beyond the standard library. Neither one
changes what it decorates: they record, and hand the class or the method back
exactly as written, so the file stays importable and testable on the author's
machine. The platform reads what they recorded when it imports the model file,
in the build pod and again in the worker.

Nothing else is re-exported. The error classes and the readers live in
``runware_serverless._endpoints`` and are not part of the published surface,
per ADR-045.
"""

from runware_serverless._endpoints import endpoint, serve

__all__ = ["endpoint", "serve"]
