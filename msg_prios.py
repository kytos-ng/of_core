"""OpenFlow message priorities used in the core queues."""

from pyof.v0x04.common.header import Type


def of_msg_prio(msg_type: int) -> int:
    """Get OpenFlow message priority.

    The lower the number the higher the priority, if same priority, then it
    will be ordered ascending by KytosEvent timestamp."""
    prios = {
        Type.OFPT_HELLO.value: -1100,
        Type.OFPT_FEATURES_REQUEST.value: -1099,
        Type.OFPT_FEATURES_REPLY.value: -1099,
        Type.OFPT_SET_CONFIG.value: -1090,
        Type.OFPT_GET_CONFIG_REPLY.value: -1090,
        Type.OFPT_GET_CONFIG_REQUEST.value: -1090,
        Type.OFPT_QUEUE_GET_CONFIG_REQUEST.value: -1090,
        Type.OFPT_QUEUE_GET_CONFIG_REPLY.value: -1090,
        Type.OFPT_ECHO_REPLY.value: -1080,
        Type.OFPT_ECHO_REQUEST.value: -1080,
        Type.OFPT_MULTIPART_REQUEST.value: -1070,
        Type.OFPT_MULTIPART_REPLY.value: -1070,
        Type.OFPT_ERROR.value: -1050,
        Type.OFPT_PACKET_IN.value: -1000,
        Type.OFPT_PORT_STATUS.value: -1000,
        Type.OFPT_FLOW_REMOVED.value: -1000,
        Type.OFPT_PACKET_OUT.value: -1000,
        Type.OFPT_PORT_MOD.value: 900,
        Type.OFPT_GROUP_MOD.value: 900,
        Type.OFPT_TABLE_MOD.value: 900,
        Type.OFPT_FLOW_MOD.value: 1000,
        Type.OFPT_BARRIER_REQUEST.value: 1000,
        Type.OFPT_BARRIER_REPLY.value: 1000,
        Type.OFPT_EXPERIMENTER.value: 1000,
    }
    return prios.get(msg_type, 0)
