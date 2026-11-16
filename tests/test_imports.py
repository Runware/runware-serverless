"""The block where a model file holds its serving-time imports.

Everything here is what a customer's own test suite would see, which on their
machine is a block that runs and hides nothing. The suppression belongs to the
platform's build and is tested in the platform's own copy of this surface.
"""

import sys

import pytest

from runware_serverless import imports


def test_the_body_runs_and_binds_its_names():
    with imports():
        import json

    assert json.dumps({"ok": True}) == '{"ok": true}'


def test_a_missing_dependency_is_the_authors_own_error():
    """The reason this package suppresses nothing.

    On the author's machine a failed import is a failed import: their traceback,
    their line. If this swallowed it, the name would stay unbound and the failure
    would surface later as a `NameError` somewhere else.
    """
    with pytest.raises(ModuleNotFoundError) as caught, imports():
        import definitely_not_a_real_distribution  # noqa: F401  # pyright: ignore[reportMissingImports]

    assert "definitely_not_a_real_distribution" in str(caught.value)


def test_a_failure_that_is_not_an_import_is_not_swallowed_either():
    with pytest.raises(ValueError, match="from the block"), imports():
        raise ValueError("from the block")


def test_the_block_leaves_no_import_behind_when_the_body_fails():
    """A half-run block binds what ran before the failure, and nothing after."""
    with pytest.raises(ModuleNotFoundError), imports():
        import decimal

        import still_not_a_real_distribution  # noqa: F401  # pyright: ignore[reportMissingImports]

    assert decimal.Decimal("1.5") * 2 == decimal.Decimal("3.0")
    assert "still_not_a_real_distribution" not in sys.modules


def test_nesting_is_the_same_as_one_block():
    with imports():  # noqa: SIM117 - the nesting is what this tests
        with imports():
            import base64

    assert base64.b64encode(b"x") == b"eA=="


def test_the_block_is_reusable_and_holds_no_state():
    block = imports()

    with block:
        import binascii

    with block:
        import colorsys

    assert binascii.hexlify(b"\x01") == b"01"
    assert colorsys.rgb_to_hls(0, 0, 0) == (0, 0, 0)
