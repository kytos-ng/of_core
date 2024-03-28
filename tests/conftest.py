"""Pytest conftest."""
# pylint: disable=redefined-outer-name
import pytest

from kytos.lib.helpers import get_controller_mock, get_switch_mock
from napps.kytos.of_core.main import Main


@pytest.fixture
def controller():
    """Controller mock fixture."""
    return get_controller_mock()


@pytest.fixture
def switch_one():
    """Switch mock fixture."""
    return get_switch_mock("00:00:00:00:00:00:00:01", 0x04)


@pytest.fixture
def napp(controller):
    """NApp fixture."""
    return Main(controller)
