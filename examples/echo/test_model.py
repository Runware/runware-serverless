"""Your own tests, written the way you would write any others.

``@serve`` and ``@endpoint`` hand the class and its methods back unchanged, so
there is nothing to mock and no test client to stand up: import the module,
make an instance, call the method.
"""

from model import EchoModel


def test_echo_reports_the_message() -> None:
    model = EchoModel()
    model.load()

    assert model.echo("hi") == {"message": "hi", "uppercase": "HI", "length": 2}


def test_reverse_applies_its_default() -> None:
    model = EchoModel()
    model.load()

    assert model.reverse_message("abc")["reversed"] == "cba"


def test_reverse_repeats() -> None:
    model = EchoModel()
    model.load()

    assert model.reverse_message("abc", repeat=2)["reversed"] == "cbacba"


def test_an_omitted_optional_arrives_as_null() -> None:
    """The platform sends an omitted optional field as an explicit ``null``.

    A Python default does not fire for that, which is why the handler applies
    it again. This is the one thing about the request shape worth pinning.
    """
    model = EchoModel()
    model.load()

    assert model.reverse_message("abc", repeat=None)["reversed"] == "cba"
