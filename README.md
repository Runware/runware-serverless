# runware-serverless

The surface you write a Runware Serverless app against: two decorators, with no dependencies in the base install.

To start, use the one-command install. It installs the CLI, or uses the CLI that you already have. If that CLI is too old, the install updates it. Then the install creates an app directory with `runware serverless init`.

macOS / Linux:

```shell
curl -fsSL https://serverless.runware.ai/install.sh | sh -s -- my-app
```

Windows (PowerShell):

```powershell
$env:RUNWARE_APP_DIR = "my-app"; irm https://serverless.runware.ai/install.ps1 | iex
```

If you already have the CLI:

```shell
runware serverless init my-app
```

`init` creates the app directory `my-app` with a `pyproject.toml`, a starter `app.py` and a `.venv` that has the package (`runware-serverless`) as a dev dependency. `init` installs nothing globally: the package goes only into the app directory's `.venv`. If `uv` is on your `PATH`, `init` uses `uv`. If not, `init` uses Python 3.10 or newer.

To use a different app name, replace `my-app` in each command. The name is also the app ID for `deploy --id`. An app ID has 6 to 30 characters: lowercase letters, digits and `-`. It starts with a letter and ends with a letter or a digit.

To log in and deploy the starter app, see the [Serverless quickstart](https://runware.ai/docs/serverless/quickstart).

To add the package to a project that you already have, install it in that project's virtual environment: run `uv add --dev runware-serverless`, or run `python -m pip install runware-serverless` with that environment active.

An app looks like this:

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

```shell
runware serverless deploy app.py --id image-tools --gpu-type h100
```

See [the Serverless documentation](https://runware.ai/docs/serverless/writing-a-model) for the whole picture. The package is only the part your editor needs.

[Runware/runware-serverless-examples](https://github.com/Runware/runware-serverless-examples) holds apps you can deploy as they are, each one the code behind a page in [the documentation](https://runware.ai/docs/serverless/examples).

## What the decorators do

**`@serve`** marks the class as the app. **`@endpoint`** marks a method as callable, at the path its own name derives: `run_upscale` serves `run-upscale`.

Neither one wraps what it decorates. Both record and hand the class or the method straight back, so your file stays importable and your own tests can instantiate the class and call its handlers directly.

`load` runs before any request reaches the worker. It is required, even when there is nothing to load, because it is part of how the platform identifies an app.

**It can run more than once.** A load that runs out of VRAM is retried with a larger request, and the retry re-instantiates your class, so both `__init__` and `load` have to be safe to repeat.

## Declaring your app's dependencies

List what your app imports beyond the standard library as a `requirements` attribute on the class:

```python
@serve
class ImageTools:
    requirements = ["torch==2.5.1", "diffusers>=0.31"]

    def load(self) -> None: ...
```

It has to be a list or tuple of strings, and the name is reserved, so a handler called `requirements` is refused.

The build reads **the first list it finds**: this attribute, then whatever the deploy passed as `--requirement`, then a `pyproject.toml` and `uv.lock` in your app directory. Declaring it on the class and on the deploy at the same time **fails the build** rather than picking one.

## What it does not do

The package holds no serving machinery, no build logic and no runtime. The base install declares no dependencies at all, so it costs you nothing and it cannot conflict with your app's own requirements.

When you deploy, Runware supplies the implementation behind these same two names. That is why the decorators record rather than execute: the marks they leave are what the platform reads when it imports your file.

You do not need to list the package in your own requirements. A deploy ignores it if you do, and serves its own copy either way.

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
they come as an extra rather than in the base install. Add the extra in the app
directory, not globally.

If `uv` is on your `PATH`, run this command in the app directory:

```shell
uv add --dev 'runware-serverless[schema]'
```

If not, install the extra with the Python in the app directory's `.venv`:

```shell
.venv/bin/python -m pip install 'runware-serverless[schema]'
```

On Windows, use `.venv\Scripts\python` in place of `.venv/bin/python`.

The `pip` command does not change `pyproject.toml`. To record the extra, find the
`runware-serverless` entry in the `dev` list under `[dependency-groups]`. Then add
`[schema]` after the name, for example `runware-serverless[schema]`.

## Configuration lives on the app

GPU type, worker counts, idle TTL and concurrency are set on the app, through the CLI, the API or the dashboard, and are changeable while it is serving. None of them are expressible in your source file, and the decorators take no arguments for them.

See [Compute and scaling](https://runware.ai/docs/serverless/compute-and-scaling).

## Python version

Python 3.10 or newer, and nothing else unless you annotate an image, which needs the `schema` extra above.

## License

MIT
