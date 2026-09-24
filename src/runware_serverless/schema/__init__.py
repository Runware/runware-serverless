try:
    from .base64_image import Base64RGBAImage, Base64RGBImage
except ImportError as err:
    message = (
        "runware_serverless.schema needs Pillow and pydantic, which the base "
        "install deliberately leaves out. Install them with: "
        "pip install runware-serverless[schema]"
    )
    raise ImportError(message) from err

__all__ = ["Base64RGBAImage", "Base64RGBImage"]
