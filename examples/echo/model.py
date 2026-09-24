"""The smallest app that works: no weights, no GPU work, two endpoints.

Reach for this one when you want to prove the loop end to end, or when
something is failing and you need to know whether it is your model or the
platform. Nothing here can be slow or run out of memory, so a failure is not
yours.
"""

from __future__ import annotations

from runware_serverless import endpoint, serve


@serve
class EchoModel:
    def load(self) -> None:
        pass

    @endpoint
    def echo(self, message: str) -> dict[str, object]:
        return {
            "message": message,
            "uppercase": message.upper(),
            "length": len(message),
        }

    @endpoint
    def reverse_message(self, message: str, repeat: int = 1) -> dict[str, object]:
        repeat = 1 if repeat is None else repeat
        return {
            "message": message,
            "reversed": message[::-1] * repeat,
        }
