"""Test msg_prios module."""

import pytest
from pyof.v0x04.common.header import Type

from napps.kytos.of_core.msg_prios import of_msg_prio


@pytest.mark.parametrize(
    "msg_type,expected_prio",
    [
        (Type.OFPT_FLOW_MOD.value, 1000),
        (Type.OFPT_BARRIER_REQUEST.value, 1000),
    ],
)
def test_of_msg_prios(msg_type, expected_prio):
    """test of_msg_prio."""
    assert of_msg_prio(msg_type) == expected_prio


def test_of_msg_default_prio():
    """test of_msg_prio default value."""
    vals = [val for val in Type.__dict__.values() if isinstance(val, int)]
    assert of_msg_prio(vals[-1].value + 1) == 0
