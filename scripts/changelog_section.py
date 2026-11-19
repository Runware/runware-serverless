"""Print one version's section of CHANGELOG.md, for the release notes.

The release workflow feeds this to `gh release create`, and a test pins the
version in pyproject.toml to a section here, so a bump without an entry fails
CI rather than publishing a release with no notes.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


def section(changelog: str, version: str) -> str | None:
    """The body under `## <version>`, or None when that heading is absent."""
    heading = re.compile(rf"^## {re.escape(version)}\s*$", re.MULTILINE)
    start = heading.search(changelog)
    if start is None:
        return None
    rest = changelog[start.end() :]
    following = re.search(r"^## ", rest, re.MULTILINE)
    body = rest if following is None else rest[: following.start()]
    return body.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="the version to print, with no leading v")
    parser.add_argument(
        "--changelog",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parents[1] / "CHANGELOG.md",
    )
    args = parser.parse_args()

    body = section(args.changelog.read_text(), args.version)
    if body is None:
        print(f"CHANGELOG.md has no '## {args.version}' section.", file=sys.stderr)
        return 1
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
