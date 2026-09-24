"""The image annotations, checked as the platform reads them.

These tests are the drift guard. The platform ships its own copy of this module
and serves that one, so a customer's local validation and their deployed schema
agree only while the two behave the same. Every assertion here is a behavior the
platform's copy has to keep.
"""

import base64
from io import BytesIO

import pydantic
import pytest
from PIL import Image

from runware_serverless.schema import Base64RGBAImage, Base64RGBImage


def encoded(mode: str = "RGBA", color: tuple[int, ...] = (10, 20, 30, 40)) -> str:
    buffer = BytesIO()
    Image.new(mode, (2, 2), color).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


class Task(pydantic.BaseModel):
    image: Base64RGBImage


class TaskWithAlpha(pydantic.BaseModel):
    image: Base64RGBAImage


def test_the_published_schema_is_a_base64_string():
    assert Task.model_json_schema()["properties"]["image"] == {
        "type": "string",
        "format": "base64",
        "description": "Image in base64 format",
        "title": "Image",
    }


def test_a_base64_payload_arrives_as_a_pil_image():
    task = Task(image=encoded())

    assert isinstance(task.image, Image.Image)
    assert task.image.size == (2, 2)


def test_rgb_drops_the_alpha_channel_and_rgba_keeps_it():
    assert Task(image=encoded()).image.mode == "RGB"
    assert TaskWithAlpha(image=encoded()).image.mode == "RGBA"


def test_an_image_passes_through_unencoded():
    image = Image.new("RGB", (2, 2))

    assert Task(image=image).image.size == (2, 2)


def test_a_malformed_payload_is_a_located_field_error():
    with pytest.raises(pydantic.ValidationError) as caught:
        Task(image="not base64 at all")

    assert caught.value.error_count() == 1
    assert caught.value.errors()[0]["loc"] == ("image",)


def test_bytes_that_decode_but_are_not_an_image_are_rejected():
    with pytest.raises(pydantic.ValidationError):
        Task(image=base64.b64encode(b"plain text").decode())


def test_a_wrong_type_is_rejected_by_name():
    with pytest.raises(pydantic.ValidationError, match="Base64RGBImage"):
        Task(image=42)
