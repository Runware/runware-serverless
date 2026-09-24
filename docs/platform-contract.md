# The contract between this package and the platform

Internal note, not customer documentation.

This package and the platform's own worker-side package expose the same two names under the same import. A customer installs this one for editor support. The platform installs its own when it builds and serves the app. The two never run together, and a deploy strips this package out of whatever reaches the image, so the platform's copy is always the one that executes.

That arrangement only holds while both agree on what a decorator leaves behind.

## What has to match

| Attribute | Where it is stamped | Read by |
| --- | --- | --- |
| `__runware_endpoint_path__` | each decorated handler | the build, to discover declared endpoints |
| `__runware_serve_options__` | the decorated class | the worker, for what `serve` was called with |
| `runware_serverless.schema` | a field of a request model | the build, to publish that field's JSON schema, and the worker, to decode what a caller sent |

Discovery is attribute-based rather than call-based: the platform reads `__runware_endpoint_path__` off the imported class instead of calling any function this package provides. That is what lets the two packages hold different versions without breaking, and it is the reason the attribute name is public.

The path derivation has to match too. A path is the method name with underscores turned into hyphens, and it has to satisfy:

```
^[a-z]([a-z0-9-]{0,62}[a-z0-9])?$
```

That pattern is held in lockstep across several places in the platform, and this package carries a copy. A copy that drifts would accept a name the platform later refuses, which turns an import-time error into a failed build.

## The image annotations are a different kind of agreement

`serve` and `endpoint` are markers. The platform reads two attribute names off
an imported class and nothing else this package does is observable, which is
what makes a version difference between a customer's copy and the platform's
survivable.

`runware_serverless.schema` is not a marker. Its behavior is the contract: the
JSON schema each type emits, what it accepts, and whether alpha survives. A
customer validates against their installed copy while the platform validates
against its own, so a drift between the two is a model whose local tests pass
and whose deployed schema describes something else.

`tests/test_schema.py` pins every one of those behaviors, and the platform's copy
has to keep them. The module body below the docstring is identical to the
platform's on purpose; only the docstring differs, because the platform's is an
internal note.

The two dependencies this needs, Pillow and pydantic, are an extra rather than a
dependency, so the base install keeps the property the package exists for.

**They only work on a field of a `pydantic.BaseModel`.** The worker binds a
handler parameter by calling `model_validate` on the model that parameter names,
so it looks for a `pydantic.BaseModel` subclass and skips anything else
(`serving/model.py`, `_model_annotation`). `Base64RGBImage` subclasses
`PIL.Image.Image`, so a bare `def handler(self, image: Base64RGBImage)` is never
coerced and the handler receives the raw string, with no validation on the way
in. Every app that uses these types puts them on a model field, which is the
shape that works. Reported as [RUNSERV-1053](https://runware.atlassian.net/browse/RUNSERV-1053),
where the bare-parameter form came from this README saying "a handler that takes
an image annotates it".

## Why this matters more here than elsewhere

The platform's compatibility mechanism between its build image and its worker image is version lockstep: both install the same pinned commit, and a test enforces it. Publishing this package breaks that property on purpose, because a customer's installed version is theirs to choose and will drift from whatever the platform is running.

Attribute-based discovery is what makes the drift survivable. It narrows the surface that has to agree down to the two attribute names and the path rule above. Nothing else this package does is observable by the platform.

## Rules that follow

- **Never rename either attribute.** Renaming one is a breaking change for every already-deployed app, not just for new installs, because the platform reads the attribute a customer's installed version stamped.
- **Never change the path derivation** without changing it in the platform in the same release.
- **Do not add a name to `__all__`** without deciding it is supportable for years. ADR-045 fixes the published surface at `serve`, `endpoint`, the `load` method, the `requirements` attribute and the handler signature convention.
- **Never let the schema types drift from the platform's copy**, and never add a type there without adding it to both. The decorators tolerate a version gap; these do not.
- **Keep the base dependency list empty.** The weight argument is the reason this package exists separately from the platform's own.

## What is deliberately absent

`requirements` is part of the published surface in ADR-045 and is not implemented anywhere yet, here or in the platform. It is tracked as RUNSERV-884 and is not MVP. When it arrives it is a class attribute the build reads, so this package will need to do nothing but document it.
