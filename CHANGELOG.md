# Changelog

## 0.3.0

### Serving-time imports

Your heavy imports can now sit at the top of the model file, in a block:

```python
from runware_serverless import endpoint, imports, serve

with imports():
    import torch
```

The build imports your file to find its endpoints, and it does that with none of your dependencies installed, so a module-level `import torch` used to fail the build and every serving import had to go inside `load` or inside a handler by hand. Inside this block the build suppresses what the import raises and names it in the build log, and the worker binds it for real.

This is what the block is for: a name you need outside a method, such as a type in an annotation or an attribute on the class. An import only one method uses is still fine where it is.

One limit worth knowing. An annotation naming a type that only exists at serving time still publishes an empty schema for that field, because the build cannot resolve the name even though your type checker now can. The endpoint serves correctly either way.

The published surface is three names now, `serve`, `endpoint` and `imports`, and the base install still declares no dependencies.

## 0.2.0

### `path` and `default` on the endpoint decorator

`@endpoint` now takes both:

```python
@endpoint(path="describe")
def describe(self, prompt: str) -> str: ...

@endpoint(default=True)
def predict(self, prompt: str) -> str: ...
```

`path` names the endpoint instead of taking the method's own name, so renaming a method no longer changes the URL your callers use. `default` marks the one endpoint that answers a request carrying no path.

Both are keyword-only, and `@endpoint` with no arguments keeps working exactly as before.

### The requirements attribute is documented

`requirements` was already read by the build. The README now says what belongs in it and why the serving dependencies go there rather than in a `pyproject.toml` the builder never reads.

## 0.1.0

### The decorators

`@serve` marks the class the platform deploys, and `@endpoint` marks a method as callable. The build imports your model file to find them and derives each endpoint's request schema from its handler signature, so the types you write are the contract you publish.

### Image annotations

A handler that takes or returns an image says so in its annotation, and the build turns that into the right schema without a wrapper type of your own.

### No dependencies

The base install declares none, on purpose. This package reaches every author's machine, so a dependency here is one they did not choose, and the release fails if one appears.
