# runware-serverless

The surface you write a Runware Serverless app against: two decorators, and nothing else to install.

```bash
pip install runware-serverless
```

```python
from runware_serverless import endpoint, serve


@serve
class ImageTools:
    def load(self) -> None:
        self.pipe = load_my_pipeline()

    @endpoint
    def generate(self, prompt: str, steps: int = 4) -> dict:
        return {"image": self.pipe(prompt, steps).encode()}
```

```bash
runware serverless deploy model.py --id image-tools --gpu-type h100
```

See [the Serverless documentation](https://runware.ai/docs/serverless/writing-a-model) for the whole picture. This package is only the part your editor needs.

[`examples/`](examples/) has two apps you can deploy as they are: the smallest one that works, and one with two endpoints whose request shapes have nothing in common.

## What the decorators do

**`@serve`** marks the class as the app. **`@endpoint`** marks a method as callable, at the path its own name derives: `run_upscale` serves `run-upscale`.

Neither one wraps what it decorates. Both record and hand the class or the method straight back, so your file stays importable and your own tests can instantiate the class and call its handlers directly.

`load` runs once per worker before any request reaches it. It is required, even when there is nothing to load, because it is part of how a deployment class is identified.

## What it does not do

This package holds no serving machinery, no build logic and no runtime. The base install declares no dependencies at all, so it costs you nothing and it cannot conflict with your model's own requirements.

When you deploy, Runware supplies the implementation behind these same two names. That is why the decorators record rather than execute: the marks they leave are what the platform reads when it imports your file.

You do not need to list this package in your own requirements. A deploy ignores it if you do, and serves its own copy either way.

## Images in a request

An image travels as a base64 string. Annotate it on a **field of a request
model**, and take that model as your handler's parameter:

```python
import pydantic
from runware_serverless import endpoint, serve
from runware_serverless.schema import Base64RGBImage


class UpscaleTask(pydantic.BaseModel):
    image: Base64RGBImage
    factor: int = 2


@serve
class Upscaler:
    def load(self) -> None: ...

    @endpoint
    def upscale(self, task: UpscaleTask) -> dict:
        return {"width": task.image.width * task.factor}
```

The platform publishes a `string` of `format: base64` for that field, decodes
what a caller sends, and `task.image` is a `PIL.Image` by the time your method
runs. A malformed payload is refused before that, as a validation error naming
the field.

**It has to be a field on a model.** A bare parameter, `def upscale(self, image:
Base64RGBImage)`, is left exactly as it arrived: the platform binds a parameter
by validating the model it names, so a parameter that is not a `pydantic.BaseModel`
is passed through untouched and your method receives the raw string.

`Base64RGBAImage` is the same thing for an image whose alpha channel has to
survive. `Base64RGBImage` converts to RGB.

These are the one part of the package with dependencies, Pillow and pydantic, so
they come as an extra rather than in the base install:

```bash
pip install 'runware-serverless[schema]'
```

## Configuration lives on the app

GPU type, worker counts, idle TTL and concurrency are set on the app, through the CLI, the API or the dashboard, and are changeable while it is serving. None of them are expressible in your source file, and the decorators take no arguments for them.

See [Compute and scaling](https://runware.ai/docs/serverless/compute-and-scaling).

## Requirements

Python 3.10 or newer, and nothing else unless you annotate an image, which needs the `schema` extra above.

## License

MIT
