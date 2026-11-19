"""The changelog has an entry for the version being published.

A release with no notes is the failure this guards: the workflow reads the
section this test proves exists, so a version bump without an entry fails here
rather than publishing a release whose body is empty.
"""

from __future__ import annotations

import pathlib
import re

import pytest
from changelog_section import section

_ROOT = pathlib.Path(__file__).parents[1]


def _version() -> str:
    # A regex, not tomllib, which 3.10 does not ship and this package supports.
    match = re.search(r'^version = "([^"]+)"', (_ROOT / "pyproject.toml").read_text(), re.MULTILINE)
    assert match is not None, "pyproject.toml declares no version"
    return match.group(1)


def test_the_current_version_has_a_section() -> None:
    version = _version()
    body = section((_ROOT / "CHANGELOG.md").read_text(), version)
    assert body is not None, f"CHANGELOG.md has no '## {version}' section"
    assert body, f"the '## {version}' section is empty"


def test_a_missing_version_is_reported_rather_than_guessed() -> None:
    assert section("# Changelog\n\n## 1.0.0\n\nfirst\n", "2.0.0") is None


def test_a_section_stops_at_the_next_version() -> None:
    changelog = "# Changelog\n\n## 2.0.0\n\nsecond\n\n## 1.0.0\n\nfirst\n"
    assert section(changelog, "2.0.0") == "second"
    assert section(changelog, "1.0.0") == "first"


@pytest.mark.parametrize("version", ["0.1.0", "0.2.0", "0.3.0"])
def test_every_released_version_is_in_the_changelog(version: str) -> None:
    assert section((_ROOT / "CHANGELOG.md").read_text(), version)
