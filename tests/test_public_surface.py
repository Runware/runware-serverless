"""What a customer can rely on, and what their own tests need to work.

The point of the public package is that a model file imports and runs on the
author's machine. These tests are the proof: every one of them does what a
customer's own test suite would do.
"""

import pytest

from runware_serverless import endpoint, serve
from runware_serverless._endpoints import (
    ENDPOINT_PATH_ATTRIBUTE,
    SERVE_OPTIONS_ATTRIBUTE,
    EndpointArgumentError,
    EndpointNameError,
    NoEndpointsError,
    endpoints,
    serve_options,
)


def test_a_customer_can_call_their_own_method_directly():
    @serve
    class ImageTools:
        def load(self) -> None:
            self.ready = True

        @endpoint
        def generate(self, prompt: str, steps: int = 4) -> dict:
            return {"prompt": prompt, "steps": steps}

    model = ImageTools()
    model.load()
    assert model.ready is True
    assert model.generate("a cat") == {"prompt": "a cat", "steps": 4}


def test_serve_returns_the_class_itself():
    class Bare:
        @endpoint
        def predict(self):
            return None

    assert serve(Bare) is Bare


def test_endpoint_returns_the_method_unwrapped():
    def handler(self, prompt: str) -> str:
        return prompt

    assert endpoint(handler) is handler
    assert handler.__annotations__ == {"prompt": str, "return": str}


def test_the_path_is_the_method_name_with_hyphens():
    @serve
    class App:
        @endpoint
        def run_upscale(self):
            return None

    assert getattr(App.run_upscale, ENDPOINT_PATH_ATTRIBUTE) == "run-upscale"
    assert set(endpoints(App)) == {"run-upscale"}


def test_the_called_form_records_its_options():
    def encode(results):
        return results

    @serve(encode_response=encode)
    class App:
        @endpoint
        def predict(self):
            return None

    assert serve_options(App).encode_response is encode


def test_the_bare_form_records_no_options():
    @serve
    class App:
        @endpoint
        def predict(self):
            return None

    assert serve_options(App) == serve_options(App)
    assert serve_options(App).encode_response is None


def test_a_subclass_serves_the_bases_endpoints():
    class Base:
        @endpoint
        def shared(self):
            return "base"

    @serve
    class Child(Base):
        @endpoint
        def own(self):
            return "child"

    assert set(endpoints(Child)) == {"shared", "own"}


def test_an_override_keeps_its_path_and_serves_itself():
    class Base:
        @endpoint
        def shared(self):
            return "base"

    @serve
    class Child(Base):
        def shared(self):
            return "child"

    assert set(endpoints(Child)) == {"shared"}
    assert endpoints(Child)["shared"](Child()) == "child"


def test_a_class_with_no_decorators_falls_back_to_predict():
    @serve
    class Legacy:
        def predict(self):
            return None

    assert set(endpoints(Legacy)) == {"predict"}


def test_a_class_with_nothing_to_serve_fails_at_import():
    with pytest.raises(NoEndpointsError):

        @serve
        class Empty:
            def helper(self):
                return None


def test_an_illegal_path_is_named_at_the_decoration_site():
    with pytest.raises(EndpointNameError):

        @endpoint
        def Generate(self):
            return None


def test_the_argument_form_is_refused():
    with pytest.raises(EndpointArgumentError):
        endpoint("run-upscale")


def test_the_options_do_not_leak_onto_a_subclass():
    @serve
    class Parent:
        @endpoint
        def predict(self):
            return None

    class Child(Parent):
        pass

    assert SERVE_OPTIONS_ATTRIBUTE not in Child.__dict__
    with pytest.raises(TypeError):
        serve_options(Child)


def test_importing_the_package_pulls_in_nothing_but_the_standard_library():
    """The reason a customer can install this next to anything they like.

    Run in a subprocess so the test session's own imports do not count.
    """
    import subprocess
    import sys

    probe = (
        "import sys, runware_serverless;"
        "print(','.join(sorted({n.split('.')[0] for n in sys.modules"
        " if not n.startswith('_')"
        " and n.split('.')[0] not in sys.stdlib_module_names"
        " and not n.startswith('runware_serverless')"
        " and n != 'sitecustomize'})))"
    )
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "", f"pulled in {out.stdout.strip()}"
