"""Two endpoints on one app, with request shapes that have nothing in common.

``generate`` takes a prompt and ``upscale`` takes an image, so no single
request schema covers both. Each handler's signature becomes its own, and the
platform routes by path.

What they do share is the app: one queue, one worker pool, one GPU type. That
is set on the app rather than here, which is why nothing in this file names
hardware or scaling. Two endpoints that genuinely need different GPUs are two
apps.

No weights and no GPU work, so this runs anywhere. The pixels are a fixed 1x1
PNG standing in for the real thing.
"""

from __future__ import annotations

from runware_serverless import endpoint, serve

PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
)
"""A 1x1 white PNG, base64. Stands in for generated pixels."""

BASE_SIZE = 64
DEFAULT_STEPS = 4
DEFAULT_SCALE = 2


@serve
class ImageTools:
    def load(self) -> None:
        pass

    @endpoint
    def generate(self, prompt: str, steps: int = DEFAULT_STEPS) -> dict[str, object]:
        # An omitted optional field arrives as an explicit null, so the default
        # is applied here as well as in the signature.
        steps = DEFAULT_STEPS if steps is None else steps
        return {
            "handler": "generate",
            "prompt": prompt,
            "steps": steps,
            "width": BASE_SIZE,
            "height": BASE_SIZE,
            "image": PIXEL_PNG,
        }

    @endpoint
    def upscale(self, image: str, scale: int = DEFAULT_SCALE) -> dict[str, object]:
        scale = DEFAULT_SCALE if scale is None else scale
        return {
            "handler": "upscale",
            "scale": scale,
            "width": BASE_SIZE * scale,
            "height": BASE_SIZE * scale,
            "image": image,
        }
