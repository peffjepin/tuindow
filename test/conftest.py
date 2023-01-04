import pytest
import contextlib


def params(names, *values):
    return pytest.mark.parametrize(names, values)


@pytest.fixture
def expect_error() -> None:
    @contextlib.contextmanager
    def inner(error_type: type, *present_in_message: str):
        with pytest.raises(error_type) as excinfo:
            yield
        for expected in present_in_message:
            assert expected in str(excinfo)
    return inner
