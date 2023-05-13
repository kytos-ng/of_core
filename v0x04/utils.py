"""Utilities module for of_core OpenFlow v0x04 operations."""
from napps.kytos.of_core.utils import aemit_message_out, emit_message_out
from pyof.v0x04.common.action import ControllerMaxLen
from pyof.v0x04.common.port import PortConfig, PortNo, PortState
from pyof.v0x04.controller2switch.common import ConfigFlag, MultipartType
from pyof.v0x04.controller2switch.multipart_request import (FlowStatsRequest,
                                                            MultipartRequest,
                                                            PortStatsRequest)
from pyof.v0x04.controller2switch.set_config import SetConfig
from pyof.v0x04.symmetric.echo_request import EchoRequest
from pyof.v0x04.symmetric.hello import Hello

from kytos.core.events import KytosEvent


def try_to_activate_interface(interface, port):
    """Try activate or deactivate an interface given a port state."""
    if any((
        port.state.value == PortState.OFPPS_LIVE,
        port.port_no.value == PortNo.OFPP_LOCAL.value
    )):
        interface.activate()
    else:
        interface.deactivate()
    return interface


def update_flow_list(controller, switch):
    """Request flow stats from switches.

    Args:
        controller(:class:`~kytos.core.controller.Controller`):
            the controller being used.
        switch(:class:`~kytos.core.switch.Switch`):
            target to send a stats request.

    Returns:
        int: multipart request xid

    """
    multipart_request = MultipartRequest()
    multipart_request.multipart_type = MultipartType.OFPMP_FLOW
    multipart_request.body = FlowStatsRequest()
    emit_message_out(controller, switch.connection, multipart_request)
    return multipart_request.header.xid


def request_port_stats(controller, switch):
    """Request port stats from switches.

    Args:
        controller(:class:`~kytos.core.controller.Controller`):
            the controller being used.
        switch(:class:`~kytos.core.switch.Switch`):
            target to send a stats request.

    Returns:
        int: multipart request xid

    """
    multipart_request = MultipartRequest()
    multipart_request.multipart_type = MultipartType.OFPMP_PORT_STATS
    multipart_request.body = PortStatsRequest()
    emit_message_out(controller, switch.connection, multipart_request)
    return multipart_request.header.xid


def update_table_list(controller, switch):
    """Request table stats from switches.

    Args:
        controller(:class:`~kytos.core.controller.Controller`):
            the controller being used.
        switch(:class:`~kytos.core.switch.Switch`):
            target to send a stats request.

    Returns:
        int: multipart request xid

    """
    multipart_request = MultipartRequest()
    multipart_request.multipart_type = MultipartType.OFPMP_TABLE
    emit_message_out(controller, switch.connection, multipart_request)
    return multipart_request.header.xid


def send_desc_request(controller, switch):
    """Request vendor-specific switch description.

    Args:
        controller(:class:`~kytos.core.controller.Controller`):
            the controller being used.
        switch(:class:`~kytos.core.switch.Switch`):
            target to send a stats request.
    """
    multipart_request = MultipartRequest()
    multipart_request.multipart_type = MultipartType.OFPMP_DESC
    emit_message_out(controller, switch.connection, multipart_request)


def send_port_request(controller, connection):
    """Send a Port Description Request after the Features Reply."""
    port_request = MultipartRequest()
    port_request.multipart_type = MultipartType.OFPMP_PORT_DESC
    emit_message_out(controller, connection, port_request)


def handle_features_reply(controller, event):
    """Handle OF v0x04 features_reply message events.

    This is the end of the Handshake workflow of the OpenFlow Protocol.

    Parameters:
        controller (Controller): Controller being used.
        event (KytosEvent): Event with features reply message.

    """
    connection = event.source
    features_reply = event.content['message']
    dpid = features_reply.datapath_id.value

    switch = controller.get_switch_or_create(dpid=dpid,
                                             connection=connection)
    send_port_request(controller, connection)

    switch.update_features(features_reply)

    return switch


async def handle_port_desc(controller, switch, port_list):
    """Update interfaces on switch based on port_list information."""
    interfaces = []
    for port in port_list:
        config = port.config
        if (port.supported == 0 and
                port.curr_speed.value == 0 and
                port.max_speed.value == 0):
            config = PortConfig.OFPPC_NO_FWD

        interface = switch.update_or_create_interface(
                        port.port_no.value,
                        name=port.name.value,
                        address=port.hw_addr.value,
                        state=port.state.value,
                        features=port.curr,
                        config=config,
                        speed=port.curr_speed.value)
        try_to_activate_interface(interface, port)
        interfaces.append(interface)

        event_name = 'kytos/of_core.switch.interface.created'
        interface_event = KytosEvent(name=event_name,
                                     content={'interface': interface})
        port_event = KytosEvent(name='kytos/of_core.switch.port.created',
                                content={
                                    'switch': switch.id,
                                    'port': port.port_no.value,
                                    'port_description': {
                                        'alias': port.name.value,
                                        'mac': port.hw_addr.value,
                                        'state': port.state.value
                                        }
                                    })
        await controller.buffers.app.aput(port_event)
        await controller.buffers.app.aput(interface_event)
    if interfaces:
        event_name = 'kytos/of_core.switch.interfaces.created'
        interface_event = KytosEvent(name=event_name,
                                     content={'interfaces': interfaces})
        await controller.buffers.app.aput(interface_event)


def send_echo(controller, switch):
    """Send echo request to a datapath.

    Keep the connection alive through symmetric echoes.
    """
    echo = EchoRequest(data=b'kytosd_13')
    emit_message_out(controller, switch.connection, echo)


def send_set_config(controller, switch):
    """Send a SetConfig message after the OpenFlow handshake."""
    set_config = SetConfig()
    set_config.flags = ConfigFlag.OFPC_FRAG_NORMAL
    set_config.miss_send_len = ControllerMaxLen.OFPCML_NO_BUFFER
    emit_message_out(controller, switch.connection, set_config)


async def say_hello(controller, connection):
    """Send back a Hello packet with the same version as the switch."""
    hello = Hello()
    await aemit_message_out(controller, connection, hello)


def mask_to_bytes(mask, size):
    """Return the mask in bytes."""
    bits = 0
    for i in range(size-mask, size):
        bits |= (1 << i)
    tobytes = bits.to_bytes(size//8, 'big')
    return tobytes


def bytes_to_mask(tobytes, size):
    """Return the mask in string."""
    int_mask = int.from_bytes(tobytes, 'big')
    strbits = format(int_mask, 'b')
    netmask = 0
    for i in range(size):
        if strbits[i] == '1':
            netmask += 1
        else:
            break
    return netmask
