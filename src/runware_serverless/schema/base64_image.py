"""Handler annotations for images that arrive as base64 on the wire.

Annotate a handler parameter with one of these and the platform publishes a
``string`` of ``format: base64`` for it, decodes what a caller sends, and hands
your method a ``PIL.Image``. The two differ only in whether an alpha channel
survives: ``Base64RGBImage`` converts to RGB, ``Base64RGBAImage`` does not.
"""

import base64
from io import BytesIO
from typing import Any

from PIL import Image
from pydantic import (
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class Base64RGBImage(Image.Image):
    """Modified PIL.Image that supports base64 parsing."""

    @classmethod
    def _from_base64(cls, data: str) -> Image.Image:
        try:
            decoded = base64.b64decode(data)
            image = Image.open(BytesIO(decoded))
        except (ValueError, OSError) as err:
            # binascii.Error (a ValueError) is what a malformed payload raises;
            # UnidentifiedImageError (an OSError) is what bytes that decoded but
            # are not an image raise. Both mean the same thing to a caller.
            message = f"Invalid base64 image: {err}"
            raise ValueError(message) from err
        return image

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _schema: core_schema.CoreSchema,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "format": "base64",
            "description": "Image in base64 format",
        }

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            function=cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v, info: f"<NOSERIAL:{cls.__name__}>" if info.mode == "json" else v,
                info_arg=True,
            ),
            json_schema_input_schema=core_schema.str_schema(),
        )

    @classmethod
    def _process(cls, image: Image.Image) -> Image.Image:
        return image.convert("RGB")

    @classmethod
    def _validate(cls, value: object) -> Image.Image:
        # ValueError, not a hand-built pydantic.ValidationError: pydantic-core
        # converts this into a located error on the field. A ValidationError
        # carrying an empty line-error list reports "0 validation errors", which
        # pydantic reads as no error at all -- the model then constructs with the
        # field silently unset, and the failure surfaces as an AttributeError
        # wherever it is first read.
        if isinstance(value, cls | Image.Image):
            return cls._process(value)
        if isinstance(value, str):
            return cls._process(cls._from_base64(value))
        message = f"Invalid type for Base64RGBImage: {type(value).__name__}"
        raise ValueError(message)


class Base64RGBAImage(Base64RGBImage):
    """Modified Base64RGBImage without converting to RGB"""

    @classmethod
    def _process(cls, image: Image.Image) -> Image.Image:
        return image  # if image is RGBA, no conversion needed
