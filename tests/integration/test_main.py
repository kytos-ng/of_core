"""Integration test main."""
# pylint: disable=wrong-import-order,protected-access
from unittest import TestCase
from unittest.mock import patch, MagicMock

from pyof.v0x04.controller2switch.features_reply import \
    FeaturesReply as FReply_v0x04
from pyof.v0x04.controller2switch.features_request import FeaturesRequest
from pyof.v0x04.controller2switch.multipart_reply import MultipartReply
from pyof.v0x04.symmetric.echo_request import EchoRequest

from kytos.core.connection import ConnectionState
from kytos.core.events import KytosEvent
from kytos.core.buffers import KytosBuffers
from kytos.lib.helpers import get_controller_mock
from napps.kytos.of_core.utils import GenericHello
from tests.helpers import (get_connection_mock, get_interface_mock,
                           get_switch_mock)


class TestAsync:
    """Test async methods from main"""

    def setup_method(self):
        """setup for napp mock"""
        # pylint: disable=import-outside-toplevel
        from napps.kytos.of_core.main import Main
        # pylint: disable=attribute-defined-outside-init
        self.napp = Main(get_controller_mock())

    @patch("time.sleep")
    def test_execute(self, mock_sleep):
        """Test 'execute' main method."""
        self.napp.controller._buffers = KytosBuffers()
        dpid_01 = "00:00:00:00:00:00:00:01"
        dpid_02 = "00:00:00:00:00:00:00:02"
        sw_04 = get_switch_mock(dpid_02)
        sw_04.connection = get_connection_mock(
            0x04, get_switch_mock(dpid_01), ConnectionState.ESTABLISHED)
        sw_ = self.napp.controller.get_switch_or_create(dpid_02,
                                                        sw_04.connection)
        sw_.is_connected = lambda: True
        sw_ = self._add_features_switch(sw_)
        # pylint: disable=protected-access
        self.napp.request_stats = self.napp._request_stats
        self.napp.execute()
        mock_sleep.assert_called()
        expected = [
            'kytos/of_core.v0x04.messages.out.ofpt_echo_request',
            'kytos/of_core.v0x04.messages.out.ofpt_multipart_request',
            'kytos/of_core.v0x04.messages.out.ofpt_multipart_request',
        ]
        for message in expected:
            of_event = self.napp.controller.buffers.msg_out.get()
            assert of_event.name == message

    def _add_features_switch(self, switch):
        """Auxiliar function to get switch mock"""
        switch.features = MagicMock()
        switch.features.capabilities = MagicMock()
        switch.features.capabilities.value = 1
        return switch

    async def test_handle_hello_raw_in(self):
        """Test handling hello raw in message."""
        self.napp.controller._buffers = KytosBuffers()
        event_name = 'kytos/core.openflow.raw.in'
        switch = get_switch_mock()
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:02"),)
        data = b'\x04\x00\x00\x10\x00\x00\x00\x3e'
        data += b'\x00\x01\x00\x08\x00\x00\x00\x10'
        event = KytosEvent(name=event_name,
                           content={'source': switch.connection,
                                    'new_data': data})
        await self.napp.on_raw_in(event)
        expected = [
            'kytos/of_core.v0x04.messages.out.ofpt_hello',
            'kytos/of_core.v0x04.messages.out.ofpt_features_request'
        ]
        for message in expected:
            of_event = self.napp.controller.buffers.msg_out.get()
            assert of_event.name == message

    async def test_handle_port_status_raw_in(self):
        """Test handling port_status raw in message."""
        self.napp.controller._buffers = KytosBuffers()
        event_name = 'kytos/core.openflow.raw.in'
        switch = get_switch_mock()
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:02"),
            ConnectionState.ESTABLISHED)

        data = b'\x04\x0c\x00\x50\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00'
        data += b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x62\x43\xe5\xdb\x35\x0a'
        data += b'\x00\x00\x73\x31\x2d\x65\x74\x68\x31\x00\x00\x00\x00\x00\x00'
        data += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x08\x40'
        data += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x98\x96'
        data += b'\x80\x00\x00\x00\x00'

        event = KytosEvent(name=event_name,
                           content={'source': switch.connection,
                                    'new_data': data})
        await self.napp.on_raw_in(event)
        of_event = await self.napp.controller.buffers.msg_in.aget()
        event = 'kytos/of_core.v0x04.messages.in.ofpt_port_status'
        assert of_event.name == event

    async def test_handle_packet_in_raw_in(self):
        """Test handling packet_in raw in message."""
        self.napp.controller._buffers = KytosBuffers()
        event_name = 'kytos/core.openflow.raw.in'
        switch = get_switch_mock()
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:02"),
            ConnectionState.ESTABLISHED)

        data = b'\x04\x0a\x00\x94\x00\x00\x00\x00\x00\x00\x00\x02\x00\x2a\x01'
        data += b'\x01\x00\x01\x02\x03\x00\x00\x00\x00\x00\x01\x00\x50\x80\x00'
        data += b'\x00\x04\x00\x00\x00\x06\x80\x00\x0a\x02\x08\x06\x80\x00\x06'
        data += b'\x06\xff\xff\xff\xff\xff\xff\x80\x00\x08\x06\xf2\x0b\xa4\x7d'
        data += b'\xf8\xea\x80\x00\x2a\x02\x00\x01\x80\x00\x2c\x04\x0a\x00\x00'
        data += b'\x01\x80\x00\x2e\x04\x0a\x00\x00\x03\x80\x00\x30\x06\xf2\x0b'
        data += b'\xa4\x7d\xf8\xea\x80\x00\x32\x06\x00\x00\x00\x00\x00\x00\x00'
        data += b'\x00\xff\xff\xff\xff\xff\xff\xf2\x0b\xa4\x7d\xf8\xea\x08\x06'
        data += b'\x00\x01\x08\x00\x06\x04\x00\x01\xf2\x0b\xa4\x7d\xf8\xea\x0a'
        data += b'\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0a\x00\x00\x03'

        event = KytosEvent(name=event_name,
                           content={'source': switch.connection,
                                    'new_data': data})
        await self.napp.on_raw_in(event)
        of_event = await self.napp.controller.buffers.msg_in.aget()
        event = 'kytos/of_core.v0x04.messages.in.ofpt_packet_in'
        assert of_event.name == event

    # pylint: disable=too-many-locals
    async def test_handle_port_desc_multipart_reply(self):
        """Test handling to ofpt_PORT_DESC."""
        self.napp.controller._buffers = KytosBuffers()
        event_name = 'kytos/of_core.v0x04.messages.in.ofpt_multipart_reply'
        switch = get_switch_mock()
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:02"))

        data = b'\x04\x13\x00\x90\x00\x00\x00\x00\x00\x0d\x00\x00\x00\x00\x00'
        data += b'\x00\x00\x00\x00\x07\x00\x00\x00\x00\xf2\x0b\xa4\xd0\x3f\x70'
        data += b'\x00\x00\x50\x6f\x72\x74\x37\x00\x00\x00\x00\x00\x00\x00\x00'
        data += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x28\x08'
        data += b'\x00\x00\x28\x00\x00\x00\x28\x08\x00\x00\x28\x08\x00\x00\x13'
        data += b'\x88\x00\x00\x13\x88\x00\x00\x00\x06\x00\x00\x00\x00\xf2\x0b'
        data += b'\xa4\x7d\xf8\xea\x00\x00\x50\x6f\x72\x74\x36\x00\x00\x00\x00'
        data += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04'
        data += b'\x00\x00\x28\x08\x00\x00\x28\x00\x00\x00\x28\x08\x00\x00\x28'
        data += b'\x08\x00\x00\x13\x88\x00\x00\x13\x88'

        port_desc = MultipartReply()
        port_desc.unpack(data[8:])
        interface_1 = get_interface_mock("interface1", 6)
        interface_2 = get_interface_mock("interface2", 7)
        switch.connection.switch.interfaces = {6: interface_1, 7: interface_2}

        stats_event = KytosEvent(name=event_name,
                                 content={'source': switch.connection,
                                          'message': port_desc})

        reply = stats_event.content['message']
        event_switch = stats_event.source.switch
        # pylint: disable=protected-access
        await self.napp._handle_multipart_reply(reply, event_switch)

        # Send port_desc pack without interface
        switch = get_switch_mock()
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:02"))
        stats_event = KytosEvent(name=event_name,
                                 content={'source': switch.connection,
                                          'message': port_desc})

        reply = stats_event.content['message']
        event_switch = stats_event.source.switch
        await self.napp._handle_multipart_reply(reply, event_switch)

        ex_switch = 'kytos/of_core.switch.port.created'
        ex_interface = 'kytos/of_core.switch.interface.created'
        ex_interfaces = 'kytos/of_core.switch.interfaces.created'
        ex_dpid = '00:00:00:00:00:00:00:02'
        ex_port = 7

        for _ in range(0, 2):
            for i in range(0, 2):
                of_event_01 = await self.napp.controller.buffers.app.aget()
                of_event_02 = await self.napp.controller.buffers.app.aget()
                assert of_event_01.name == ex_switch
                assert of_event_01.content['switch'] == ex_dpid
                assert of_event_01.content['port'] == ex_port - i
                assert of_event_02.name == ex_interface
                assert getattr(of_event_02.content['interface'],
                               'port_number') == ex_port - i

            of_event_01 = await self.napp.controller.buffers.app.aget()
            assert of_event_01.name == ex_interfaces
            assert len(of_event_01.content['interfaces']) == 2

    async def test_handle_multipart_reply(self):
        """Test handling ofpt_multipart_reply."""
        self.napp.controller._buffers = KytosBuffers()
        event_name = 'kytos/of_core.v0x04.messages.in.ofpt_multipart_reply'
        switch = get_switch_mock("00:00:00:00:00:00:00:02")
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:01"),
            ConnectionState.ESTABLISHED)

        self.napp.controller.get_switch_or_create(switch.dpid,
                                                  switch.connection)

        data = b'\x04\x13\x00\x68\xac\xc8\xdf\x58\x00\x01\x00\x00\x00\x00\x00'
        data += b'\x00\x00\x58\x00\x00\x00\x00\x00\x38\x25\xd9\x54\xc0\x03\xe8'
        data += b'\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x12\x00\x00\x00\x00'
        data += b'\x00\x00\x02\xf4\x00\x01\x00\x10\x80\x00\x0a\x02\x88\xcc\x80'
        data += b'\x00\x0c\x02\x1e\xd7\x00\x04\x00\x18\x00\x00\x00\x00\x00\x00'
        data += b'\x00\x10\xff\xff\xff\xfd\xff\xff\x00\x00\x00\x00\x00\x00'

        # pylint: disable=protected-access
        xid = self.napp._multipart_replies_xids[switch.dpid]["flows"]
        # pylint: enable=protected-access
        multipart_reply = MultipartReply(xid=xid)
        multipart_reply.unpack(data[8:])
        stats_event = KytosEvent(name=event_name,
                                 content={'source': switch.connection,
                                          'message': multipart_reply})
        reply = stats_event.content['message']
        event_switch = stats_event.source.switch
        # pylint: disable=protected-access
        await self.napp._handle_multipart_reply(reply, event_switch)

        # test ofpmp_desc
        data = b'\x04\x12\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        data += b'\x00'
        multipart_desc = MultipartReply()
        multipart_desc.unpack(data[8:])
        stats_desc_event = KytosEvent(name=event_name,
                                      content={'source': switch.connection,
                                               'message': multipart_desc})

        target_switch = switch.connection.switch
        reply = stats_desc_event.content['message']
        event_switch = stats_desc_event.source.switch
        await self.napp._handle_multipart_reply(reply, event_switch)
        # pylint: disable=protected-access
        assert xid not in self.napp._multipart_replies_xids
        assert len(target_switch.flows) > 0
        assert (multipart_desc.body.mfr_desc.value ==
                target_switch.description["manufacturer"])
        assert (multipart_desc.body.hw_desc.value ==
                target_switch.description["hardware"])
        assert (multipart_desc.body.sw_desc.value ==
                target_switch.description["software"])
        assert (multipart_desc.body.serial_num.value ==
                target_switch.description["serial"])
        assert (multipart_desc.body.dp_desc.value ==
                target_switch.description["data_path"])


class TestMain(TestCase):
    """Class to Integration test kytos/of_core main."""

    def setUp(self):
        """Execute steps before each tests.
        Set the server_name_url from kytos/of_core
        """
        self.server_name_url = 'http://localhost:8181/api/kytos/of_core'

        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        # pylint: disable=import-outside-toplevel
        from napps.kytos.of_core.main import Main
        self.addCleanup(patch.stopall)

        self.napp = Main(get_controller_mock())
        self.patched_events = []

    def test_get_event_listeners(self):
        """Verify all event listeners registered"""
        expected_events = [
            'kytos/of_core.v0x04.messages.in.ofpt_features_reply',
            'kytos/of_core.v0x04.messages.out.ofpt_features_request',
            'kytos/core.openflow.raw.in',
            'kytos/of_core.v0x04.messages.in.ofpt_echo_request',
            'kytos/of_core.v0x04.messages.out.ofpt_echo_reply',
            'kytos/of_core.v0x[0-9a-f]{2}.messages.in.hello_failed',
            'kytos/of_core.v0x04.messages.out.hello_failed',
            'kytos/core.shutdown',
            'kytos/core.shutdown.kytos/of_core',
            'kytos/of_core.handshake.completed',
        ]

        actual_events = self.napp.listeners()
        for _event in expected_events:
            self.assertIn(_event, actual_events, str(_event))

    def test_handle_04_features_reply(self):
        """Test handling features reply message."""
        self.napp.controller._buffers = KytosBuffers()
        event_name = 'kytos/of_core.v0x04.messages.in.ofpt_features_reply'
        switch = get_switch_mock()
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:02"),
            ConnectionState.SETUP)
        switch.connection.protocol.state = 'waiting_features_reply'

        data = b'\x04\x06\x00\x20\x00\x00\x00\x00\x00\x00\x08\x60\x6e\x7f\x74'
        data += b'\xe7\x00\x00\x00\x00\xff\x63\x00\x00\x00\x00\x00\x4f\x00\x00'
        data += b'\x00\x00'

        features_reply = FReply_v0x04()
        features_reply.unpack(data[8:])

        event = KytosEvent(name=event_name,
                           content={'source': switch.connection,
                                    'message': features_reply})
        self.napp.handle_features_reply(event)
        target_switch = '00:00:08:60:6e:7f:74:e7'
        of_event_01 = self.napp.controller.buffers.app.get()
        of_event_02 = self.napp.controller.buffers.app.get()
        self.assertEqual("kytos/core.switch.new", of_event_01.name)
        self.assertEqual(target_switch, of_event_01.content["switch"].dpid)
        self.assertEqual("kytos/of_core.handshake.completed", of_event_02.name)
        self.assertEqual(target_switch, of_event_02.content["switch"].dpid)
        expected = [
            'kytos/of_core.v0x04.messages.out.ofpt_set_config',
            'kytos/of_core.v0x04.messages.out.ofpt_multipart_request',
            'kytos/of_core.v0x04.messages.out.ofpt_multipart_request'
        ]

        for message in expected:
            of_event = self.napp.controller.buffers.msg_out.get()
            self.assertEqual(of_event.name, message)

    def test_handle_features_request_sent(self):
        """Test handling features request sent message."""
        event_name = 'kytos/of_core.v0x04.messages.out.ofpt_features_request'
        switch = get_switch_mock()
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:02"))
        switch.connection.protocol.state = 'sending_features'

        data = b'\x04\x05\x00\x08\x00\x00\x00\x03'
        features_request = FeaturesRequest()
        features_request.unpack(data)

        event = KytosEvent(name=event_name,
                           content={'destination': switch.connection,
                                    'message': features_request})
        self.napp.handle_features_request_sent(event)
        self.assertEqual(event.destination.protocol.state,
                         'waiting_features_reply')

    def test_handle_echo_request(self):
        """Test handling echo request message."""
        self.napp.controller._buffers = KytosBuffers()
        event_name = 'kytos/of_core.v0x04.messages.in.ofpt_echo_request'
        switch = get_switch_mock()
        switch.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:02"))

        data = b'\x04\x02\x00\x0c\x00\x00\x00\x00\x68\x6f\x67\x65'
        echo_request = EchoRequest()
        echo_request.unpack(data)

        event = KytosEvent(name=event_name,
                           content={'source': switch.connection,
                                    'message': echo_request})
        self.napp.handle_echo_request(event)
        of_event = self.napp.controller.buffers.msg_out.get()
        self.assertEqual(of_event.name,
                         'kytos/of_core.v0x04.messages.out.ofpt_echo_reply')

    def test_pack_generic_hello(self):
        """Test packing a generic hello message."""
        data = b'\x04\x00\x00\x10\x00\x00\x00\x3e'
        data += b'\x00\x01\x00\x08\x00\x00\x00\x10'
        generic_hello = GenericHello(packet=data, versions=b'\x04')
        self.assertEqual(generic_hello.pack(), data)
