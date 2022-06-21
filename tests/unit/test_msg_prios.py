"""Test msg_prios module."""

import pytest
from pyof.v0x04.common.header import Type

from napps.kytos.of_core.msg_prios import of_msg_prio


@pytest.mark.parametrize(
    "msg_type,expected_prio",
    [
        (Type.OFPT_HELLO.value, -1100),
        (Type.OFPT_FEATURES_REQUEST.value, -1099),
        (Type.OFPT_FEATURES_REPLY.value, -1099),
        (Type.OFPT_SET_CONFIG.value, -1090),
        (Type.OFPT_GET_CONFIG_REPLY.value, -1090),
        (Type.OFPT_GET_CONFIG_REQUEST.value, -1090),
        (Type.OFPT_QUEUE_GET_CONFIG_REQUEST.value, -1090),
        (Type.OFPT_QUEUE_GET_CONFIG_REPLY.value, -1090),
        (Type.OFPT_ECHO_REPLY.value, -1080),
        (Type.OFPT_ECHO_REQUEST.value, -1080),
        (Type.OFPT_MULTIPART_REQUEST.value, -1070),
        (Type.OFPT_MULTIPART_REPLY.value, -1070),
        (Type.OFPT_ERROR.value, -1050),
        (Type.OFPT_PACKET_IN.value, -1000),
        (Type.OFPT_PORT_STATUS.value, -1000),
        (Type.OFPT_FLOW_REMOVED.value, -1000),
        (Type.OFPT_PACKET_OUT.value, -1000),
        (Type.OFPT_PORT_MOD.value, 900),
        (Type.OFPT_GROUP_MOD.value, 900),
        (Type.OFPT_TABLE_MOD.value, 900),
        (Type.OFPT_FLOW_MOD.value, 1000),
        (Type.OFPT_BARRIER_REQUEST.value, 1000),
        (Type.OFPT_BARRIER_REPLY.value, 1000),
        (Type.OFPT_EXPERIMENTER.value, 1000),
    ],
)
def test_of_msg_prios(msg_type, expected_prio):
    """test of_msg_prio."""
    assert of_msg_prio(msg_type) == expected_prio


def test_of_msg_default_prio():
    """test of_msg_prio default value."""
    vals = [val for val in Type.__dict__.values() if isinstance(val, int)]
    assert of_msg_prio(vals[-1].value + 1) == 0
