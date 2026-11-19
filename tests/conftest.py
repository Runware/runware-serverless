"""Put `scripts/` on the path, so a test can import the release helpers."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "scripts"))
