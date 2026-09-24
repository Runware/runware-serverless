# Examples

Two apps you can deploy as they are. Both are deliberately trivial, with no weights and no GPU work, so they build and run anywhere and a failure in one is the platform rather than the model.

## `echo`

The smallest app that works: two endpoints, and a handler that returns what you sent it.

```bash
cd echo
runware serverless deploy model.py --id echo --gpu-type l40s
```

Reach for it when something is failing and you need to know whether the problem is your model or the platform. Nothing in it can be slow or run out of memory.

## `image-tools`

Two endpoints whose request shapes have nothing in common: `generate` takes a prompt, `upscale` takes an image.

```bash
cd image-tools
runware serverless deploy model.py --id image-tools --gpu-type l40s
```

It is the one to read if you are deciding how to split your work up. Both endpoints share one queue, one worker pool and one GPU type, because those belong to the app rather than to the endpoint. Two endpoints that genuinely need different hardware are two apps.

## Running the tests

`@serve` and `@endpoint` return the class and the method unchanged, so a test is a test. There is no client to stand up and nothing to mock.

```bash
pip install runware-serverless pytest
cd echo && python -m pytest
```

## Where the weights go

Neither example loads any, so neither shows the thing that matters most for a real model: **what you download in `load` should land on a volume**, not on the sandbox filesystem.

```python
import os

_CACHE = "/root/.cache/huggingface"


@serve
class MyModel:
    def load(self) -> None:
        if hasattr(self, "pipeline"):
            return
        self.pipeline = SomePipeline.from_pretrained(REPO, cache_dir=_CACHE).to("cuda")
```

```bash
runware serverless deploy model.py --id my-model --gpu-type h100 \
  --volume /root/.cache/huggingface
```

Two things are doing work there. The **volume** keeps the weights across cold starts, so you are not paying GPU time to fetch them again. The **`hasattr` guard** makes `load` safe to run twice, which it has to be: it is retried if the GPU runs out of memory at startup.

See [Volumes](https://runware.ai/docs/serverless/volumes) and [Writing a model](https://runware.ai/docs/serverless/writing-a-model).
