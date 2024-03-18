"""Test Main methods."""
from unittest.mock import (AsyncMock, MagicMock, PropertyMock, create_autospec,
                           patch)

import pytest
from napps.kytos.of_core.utils import NegotiationException
from pyof.foundation.network_types import Ethernet
from pyof.v0x04.common.port import PortState
from pyof.v0x04.controller2switch.common import MultipartType

from kytos.core.connection import ConnectionState
from kytos.lib.helpers import (get_connection_mock, get_controller_mock,
                               get_kytos_event_mock, get_switch_mock)

# pylint: disable=protected-access, invalid-name


class TestNApp:
    """Test NApp Main class, pytest test suite. """

    @patch('napps.kytos.of_core.main.Main.process_multipart_messages')
    @patch('napps.kytos.of_core.main.of_slicer')
    @patch('napps.kytos.of_core.main.Main._negotiate')
    @patch('napps.kytos.of_core.main.Main.aemit_message_in')
    async def test_on_raw_in(
        self,
        mock_aemit_message_in,
        mock_negotiate,
        mock_of_slicer,
        mock_process_multipart_messages,
        napp,
    ):
        """Test on_raw_in."""

        mock_packets = MagicMock()
        mock_data = MagicMock()
        mock_connection = MagicMock()
        mock_connection.is_new.side_effect = [True, False, True, False]
        mock_connection.is_during_setup.return_value = False
        mock_of_slicer.return_value = [[mock_packets, mock_packets], b'']
        name = 'kytos/core.openflow.raw.in'
        content = {'source': mock_connection, 'new_data': mock_data}
        mock_event = get_kytos_event_mock(name=name, content=content)

        await napp.on_raw_in(mock_event)
        mock_negotiate.assert_called()
        mock_aemit_message_in.assert_called()

        # Test Fail
        mock_negotiate.side_effect = NegotiationException('Foo')
        await napp.on_raw_in(mock_event)
        assert mock_connection.close.call_count == 1

        mock_connection.close.call_count = 0
        mock_connection.protocol.unpack.side_effect = AttributeError()
        await napp.on_raw_in(mock_event)
        assert mock_connection.close.call_count == 1

        # test message type OFPT_MULTIPART_REPLY
        mock_message = MagicMock()
        mock_message.header.xid = 0xABC
        mock_message.header.message_type.name = 'ofpt_multipart_reply'
        mock_connection.protocol.unpack.side_effect = [mock_message]*2
        mock_connection.is_new.side_effect = [False, False]
        mock_process_multipart_messages.call_count = 0
        messages = {0xABC: [mock_message]*2}
        await napp.on_raw_in(mock_event)
        mock_process_multipart_messages.assert_called_with(mock_connection,
                                                           messages)

    @patch('pyof.utils.v0x04.asynchronous.error_msg.ErrorMsg')
    async def test_fail_negotiation(
        self,
        mock_error_msg,
        napp
    ):
        """Test fail_negotiation."""
        mock_aemit_message_out = AsyncMock()
        mock_event_buffer = AsyncMock()
        napp.aemit_message_out = mock_aemit_message_out
        napp.controller._buffers.app.aput = mock_event_buffer

        mock_connection = MagicMock()
        mock_message = MagicMock()
        mock_connection.id = "A"
        mock_message.side_effect = 4
        await napp.fail_negotiation(mock_connection, mock_message)
        mock_event_buffer.assert_called()
        mock_aemit_message_out.assert_called_with(mock_connection,
                                                  mock_error_msg.return_value)

    @patch('napps.kytos.of_core.main.Main.send_features_request')
    @patch('napps.kytos.of_core.v0x04.utils.say_hello')
    @patch('napps.kytos.of_core.main._get_version_from_bitmask')
    @patch('napps.kytos.of_core.main._get_version_from_header')
    async def test_negotiate(
        self,
        mock_version_header,
        mock_version_bitmask,
        mock_say_hello,
        mock_features_request,
        napp
    ):
        """Test negotiate."""
        napp.controller._buffers.app.aput = AsyncMock()
        napp.controller._buffers.msg_out.aput = AsyncMock()
        mock_version_header.return_value = 4
        mock_version_bitmask.side_effect = [4, None]
        mock_connection = MagicMock()
        mock_message = MagicMock()
        type(mock_message).versions = PropertyMock(side_effect=[4, 4, 4,
                                                                False])

        await napp._negotiate(mock_connection, mock_message)
        mock_version_bitmask.assert_called_with(mock_message.versions)
        mock_say_hello.assert_called_with(napp.controller,
                                          mock_connection)
        mock_features_request.assert_called_with(mock_connection)

        await napp._negotiate(mock_connection, mock_message)
        mock_say_hello.assert_called_with(napp.controller,
                                          mock_connection)
        mock_features_request.assert_called_with(mock_connection)

        # Test Fail
        with pytest.raises(NegotiationException):
            type(mock_message).versions = PropertyMock(return_value=[4])
            await napp._negotiate(mock_connection, mock_message)

    @patch('pyof.utils.v0x04.controller2switch.'
           'features_request.FeaturesRequest')
    @patch('napps.kytos.of_core.main.Main.aemit_message_out')
    async def test_send_features_request(
        self,
        mock_emit_message_out,
        mock_features_request,
        napp
    ):
        """Test send send_features_request."""
        mock_destination = MagicMock()
        mock_destination.protocol.version = 4
        mock_features_request.return_value = "A"
        await napp.send_features_request(mock_destination)
        mock_features_request.assert_called()
        mock_emit_message_out.assert_called_with(mock_destination, "A")

    @patch('napps.kytos.of_core.settings.SEND_FEATURES_REQUEST_ON_ECHO')
    @patch('napps.kytos.of_core.main.Main.send_features_request')
    async def test_on_queued_openflow_echo_reply(
        self,
        mock_send_features_request,
        mock_settings,
        napp
    ):
        """Test handle queued OpenFlow echo reply messages."""
        mock_settings.return_value = True
        mock_event = MagicMock()
        await napp.on_queued_openflow_echo_reply(mock_event)
        mock_send_features_request.assert_called_with(mock_event.destination)

    @patch('napps.kytos.of_core.main.Main._handle_multipart_reply')
    @patch('napps.kytos.of_core.main.Main.aemit_message_in')
    async def test_process_multipart_messages(
        self,
        mock_aemit_message_in,
        mock_handle_multipart_reply,
        switch_one,
        napp
    ):
        """Test process_multipart_messages."""
        dpid = switch_one.id
        mock_connection = MagicMock()
        mock_connection.switch = switch_one
        napp._multipart_replies_xids = {dpid: {0xABC: 0}}
        mock_message = MagicMock()
        messages = {0xABC: [mock_message]*2}
        await napp.process_multipart_messages(mock_connection, messages)
        assert mock_aemit_message_in.call_count == len(messages[0xABC])
        assert mock_handle_multipart_reply.call_count == len(messages[0xABC])

    @patch('napps.kytos.of_core.main.Main._handle_multipart_table_stats')
    @patch('napps.kytos.of_core.main.Main._handle_multipart_flow_stats')
    @patch('napps.kytos.of_core.v0x04.utils.handle_port_desc')
    async def test_handle_multipart_reply(
        self,
        mock_of_core_v0x04_utils,
        mock_from_of_flow_stats_v0x04,
        mock_from_of_table_stats,
        switch_one,
        napp,
    ):
        """Test handle multipart reply."""
        flow_msg = MagicMock()
        flow_msg.multipart_type = MultipartType.OFPMP_FLOW
        await napp._handle_multipart_reply(flow_msg, switch_one)
        mock_from_of_flow_stats_v0x04.assert_called_with(
            flow_msg, switch_one.connection.switch)

        table_msg = MagicMock()
        table_msg.multipart_type = MultipartType.OFPMP_TABLE
        await napp._handle_multipart_reply(table_msg, switch_one)
        mock_from_of_table_stats.assert_called_with(
            table_msg, switch_one.connection.switch)

        ofpmp_port_desc = MagicMock()
        ofpmp_port_desc.body = "A"
        ofpmp_port_desc.multipart_type = MultipartType.OFPMP_PORT_DESC
        await napp._handle_multipart_reply(ofpmp_port_desc, switch_one)
        mock_of_core_v0x04_utils.assert_called_with(
            napp.controller, switch_one.connection.switch,
            ofpmp_port_desc.body)

        ofpmp_desc = MagicMock()
        ofpmp_desc.body = "A"
        ofpmp_desc.multipart_type = MultipartType.OFPMP_DESC
        await napp._handle_multipart_reply(ofpmp_desc, switch_one)
        assert switch_one.update_description.call_count == 1

    @patch('napps.kytos.of_core.main.log')
    @patch('napps.kytos.of_core.main.Main._update_switch_flows')
    @patch('napps.kytos.of_core.v0x04.flow.Flow.from_of_flow_stats')
    @patch('napps.kytos.of_core.main.Main._is_multipart_reply_ours')
    async def test_on_multipart_flow_stats(
        self,
        mock_is_multipart_reply_ours,
        mock_from_of_flow_stats_v0x04,
        mock_update_switch_flows,
        mock_log,
        switch_one,
        napp
    ):
        """Test on multipart flow stats."""
        mock_is_multipart_reply_ours.return_value = True
        mock_from_of_flow_stats_v0x04.return_value = "ABC"

        mock_buffer_aput = AsyncMock()
        napp.controller._buffers.app.aput = mock_buffer_aput

        flow_msg = MagicMock()
        flow_msg.body = "A"
        flow_msg.flags.value = 2
        flow_msg.body_type = MultipartType.OFPMP_FLOW
        flow_msg.header.xid = 0xABC

        dpid = switch_one.id
        xid_flows = 0xABC
        napp._multipart_replies_xids = {dpid: {'flows': xid_flows}}

        await napp._handle_multipart_flow_stats(flow_msg, switch_one)

        mock_is_multipart_reply_ours.assert_called_with(flow_msg,
                                                        switch_one,
                                                        'flows')
        mock_from_of_flow_stats_v0x04.assert_called_with(flow_msg.body,
                                                         switch_one)
        mock_update_switch_flows.assert_called_with(switch_one)
        assert mock_buffer_aput.call_count == 1
        kytos_event = mock_buffer_aput.call_args[0][0]
        assert kytos_event.name == 'kytos/of_core.flow_stats.received'
        assert kytos_event.content['switch'] == switch_one
        assert "replies_flows" in kytos_event.content

        # Test when update_switch_flows fails
        mock_update_switch_flows.side_effect = KeyError()
        mock_buffer_aput.call_count = 0
        mock_log.error.call_count = 0
        await napp._handle_multipart_flow_stats(flow_msg, switch_one)
        assert mock_log.error.call_count == 1
        mock_buffer_aput.assert_not_called()

    @patch('napps.kytos.of_core.table.TableStats.from_of_table_stats')
    @patch('napps.kytos.of_core.main.Main._is_multipart_reply_ours')
    async def test_on_multipart_table_stats(
        self,
        mock_is_multipart_reply_ours,
        mock_from_of_table_stats,
        switch_one,
        napp
    ):
        """Test on multipart table stats."""
        mock_is_multipart_reply_ours.return_value = True

        mock_buffer_aput = AsyncMock()
        napp.controller._buffers.app.aput = mock_buffer_aput

        table_msg = MagicMock()
        table_msg.body = "A"
        table_msg.flags.value = 2
        table_msg.body_type = MultipartType.OFPMP_TABLE
        table_msg.header.xid = 0xABC

        dpid = switch_one.id
        xid_tables = 0xABC
        napp._multipart_replies_xids = {dpid: {'tables': xid_tables}}

        await napp._handle_multipart_table_stats(table_msg, switch_one)

        mock_is_multipart_reply_ours.assert_called_with(table_msg,
                                                        switch_one,
                                                        'tables')
        mock_from_of_table_stats.assert_called_with(table_msg.body,
                                                    switch_one)
        assert mock_buffer_aput.call_count == 1
        kytos_event = mock_buffer_aput.call_args[0][0]
        assert kytos_event.name == 'kytos/of_core.table_stats.received'
        assert kytos_event.content['switch'] == switch_one
        assert "replies_tables" in kytos_event.content

    @patch('napps.kytos.of_core.main.Main._new_port_stats')
    @patch('napps.kytos.of_core.main.Main._is_multipart_reply_ours')
    async def test_handle_multipart_port_stats(
        self,
        mock_is_multipart_reply_ours,
        mock_new_port_stats,
        switch_one,
        napp,
    ):
        """Test handle multipart flow stats."""
        mock_is_multipart_reply_ours.return_value = True

        port_stats_msg = MagicMock()
        port_stats_msg.body = "A"
        port_stats_msg.flags.value = 2
        port_stats_msg.multipart_type = MultipartType.OFPMP_PORT_STATS

        await napp._handle_multipart_port_stats(port_stats_msg,
                                                switch_one)

        mock_is_multipart_reply_ours.assert_called_with(port_stats_msg,
                                                        switch_one,
                                                        'ports')
        mock_new_port_stats.assert_called_with(switch_one)

    @patch('napps.kytos.of_core.main.Main.update_port_status')
    @patch('napps.kytos.of_core.main.Main.update_links')
    async def test_aemit_message_in(
        self,
        mock_update_links,
        mock_update_port_status,
        napp
    ):
        """Test aemit_message_in."""
        napp.controller._buffers.msg_in.aput = AsyncMock()
        mock_port_connection = MagicMock()
        msg_port_mock = MagicMock()
        msg_port_mock.header.message_type.name = 'ofpt_port_status'
        mock_port_connection.side_effect = True
        await napp.aemit_message_in(mock_port_connection,
                                    msg_port_mock)
        mock_update_port_status.assert_called_with(msg_port_mock,
                                                   mock_port_connection)

        mock_packet_in_connection = MagicMock()
        msg_packet_in_mock = MagicMock()
        mock_packet_in_connection.side_effect = True
        msg_packet_in_mock.header.message_type.name = 'ofpt_packet_in'
        await napp.aemit_message_in(mock_packet_in_connection,
                                    msg_packet_in_mock)
        mock_update_links.assert_called_with(msg_packet_in_mock,
                                             mock_packet_in_connection)

    async def test_emit_message_out(self, napp):
        """Test emit message_out."""
        mock_aemit_message_out = AsyncMock()
        napp.controller._buffers.msg_out.aput = mock_aemit_message_out
        mock_connection = MagicMock()
        mock_message = MagicMock()
        mock_connection.is_alive.return_value = True
        await napp.aemit_message_out(mock_connection, mock_message)
        mock_aemit_message_out.assert_called()

    async def test_on_openflow_connection_error(self, napp) -> None:
        """Test on_openflow_connection_error."""
        dpid = "1"
        event, switch = MagicMock(), MagicMock(id=dpid)
        event.content["destination"].switch = switch
        napp._multipart_replies_xids[dpid] = {"flows": 2, "ports": 3}
        napp._multipart_replies_flows[dpid] = [MagicMock()]
        napp._multipart_replies_ports[dpid] = [MagicMock()]
        await napp.on_openflow_connection_error(event)
        assert dpid not in napp._multipart_replies_xids
        assert dpid not in napp._multipart_replies_flows
        assert dpid not in napp._multipart_replies_ports

    async def test_on_openflow_connection_error_no_sw(self, napp) -> None:
        """Test on_openflow_connection_error no switch."""
        event = MagicMock()
        napp.pop_multipart_replies = MagicMock()
        event.content["destination"].switch = None
        await napp.on_openflow_connection_error(event)
        assert napp.pop_multipart_replies.call_count == 0


# pylint: disable=attribute-defined-outside-init
# pylint: disable=import-outside-toplevel
class TestMain:
    """Test the Main class."""

    @pytest.fixture(autouse=True)
    def commomn_patches(self, request):
        """This function handles setup and cleanup for patches"""
        # This fixture sets up the common patches,
        # and a finalizer is added using addfinalizer to stop
        # the common patches after each test. This ensures that the cleanup
        # is performed after each test, and additional patch decorators
        # can be used within individual test functions.

        patcher = patch("kytos.core.helpers.run_on_thread", lambda x: x)
        mock_patch = patcher.start()

        _ = request.function.__name__

        def cleanup():
            patcher.stop()

        request.addfinalizer(cleanup)
        return mock_patch

    def setup_method(self):
        """Execute steps before each tests.
        Set the server_name_url from kytos/of_core
        """
        self.switch_v0x04 = get_switch_mock("00:00:00:00:00:00:00:02", 0x04)
        self.switch_v0x04.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:04"))

        from napps.kytos.of_core.main import Main
        self.napp = Main(get_controller_mock())

    @patch('napps.kytos.of_core.v0x04.utils.send_echo')
    def test_execute(self, mock_of_core_v0x04_utils):
        """Test execute."""
        self.napp.request_stats = MagicMock()
        self.switch_v0x04.is_connected.return_value = True

        self.napp.controller.switches = {"00:00:00:00:00:00:00:01":
                                         self.switch_v0x04}
        self.napp.execute()
        mock_of_core_v0x04_utils.assert_called()
        assert self.napp.request_stats.call_count == 1

    def _add_features_switch(self, switch):
        """Auxiliar function to get switch mock"""
        switch.features = MagicMock()
        switch.features.capabilities = MagicMock()
        switch.features.capabilities.value = 2
        return switch

    @patch('napps.kytos.of_core.main.settings')
    def test_check_overlapping_multipart_request(self, mock_settings):
        """Test check_overlapping_multipart_request."""
        mock_settings.STATS_REQ_SKIP = 3
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_switch.id = dpid

        # Case 1: skipped due to delayed flow stats
        self.napp._multipart_replies_xids = {dpid: {'flows': 0xABC}}
        assert self.napp._check_overlapping_multipart_request(mock_switch)
        assert self.napp._multipart_replies_xids[dpid]['skipped'] == 1

        # Case 2: skipped due to delayed port stats
        self.napp._multipart_replies_xids = {dpid: {'ports': 0xABC,
                                                    'skipped': 1}}
        assert self.napp._check_overlapping_multipart_request(mock_switch)
        assert self.napp._multipart_replies_xids[dpid]['skipped'] == 2

        # Case 3: delayed port or flow stats but already skipped X times
        self.napp._multipart_replies_flows = {dpid: mock_switch}
        self.napp._multipart_replies_ports = {dpid: mock_switch}
        self.napp._multipart_replies_xids = {dpid: {'flows': 0xABC,
                                                    'ports': 0xABC,
                                                    'skipped': 3}}
        assert not self.napp._check_overlapping_multipart_request(mock_switch)
        assert not self.napp._multipart_replies_flows
        assert not self.napp._multipart_replies_ports

    @patch('napps.kytos.of_core.main.settings')
    def test_get_switch_req_stats_delay(self, mock_settings):
        """Test _get_switch_req_stats_delay."""
        mock_settings.STATS_INTERVAL = 60
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_switch.id = dpid

        # Case 1: switch already known
        self.napp.switch_req_stats_delay = {dpid: 9}
        assert self.napp._get_switch_req_stats_delay(mock_switch) == 9

        # Case 2: switch unknown, it should have a new delay based on
        # STATS_INTERVAL
        self.napp.switch_req_stats_delay = {}
        assert self.napp._get_switch_req_stats_delay(mock_switch) == 3

        # Case 3: switch unknown but there are other switches, it should have
        # a new delay based on STATS_INTERVAL and different from others
        dpid2 = '00:00:00:00:00:00:00:02'
        mock_sw2 = get_switch_mock(dpid2)
        mock_sw2.id = dpid2
        self.napp.switch_req_stats_delay = {dpid: 3, 'last': 3}
        assert self.napp._get_switch_req_stats_delay(mock_sw2) == 6

    @patch('time.sleep', return_value=None)
    @patch('napps.kytos.of_core.main.Main.'
           '_check_overlapping_multipart_request')
    @patch('napps.kytos.of_core.v0x04.utils.update_flow_list')
    @patch('napps.kytos.of_core.v0x04.utils.request_table_stats')
    def test_request_stats(self, *args):
        """Test request flow list."""
        (mock_request_table_stats_v0x4, mock_update_flow_list_v0x04,
            mock_check_overlapping_multipart_request, _) = args
        mock_update_flow_list_v0x04.return_value = 0xABC
        mock_check_overlapping_multipart_request.return_value = False
        self.switch_v0x04 = self._add_features_switch(self.switch_v0x04)
        self.napp._request_stats(self.switch_v0x04)
        mock_update_flow_list_v0x04.assert_called_with(self.napp.controller,
                                                       self.switch_v0x04)
        mock_request_table_stats_v0x4.return_value = 0xABC
        mock_request_table_stats_v0x4.assert_called_with(self.napp.controller,
                                                         self.switch_v0x04)

        mock_update_flow_list_v0x04.call_count = 0
        mock_check_overlapping_multipart_request.return_value = True
        self.napp._request_stats(self.switch_v0x04)
        mock_update_flow_list_v0x04.assert_not_called()

    @patch('time.sleep', return_value=None)
    @patch('napps.kytos.of_core.main.Main.'
           '_check_overlapping_multipart_request')
    @patch('napps.kytos.of_core.v0x04.utils.request_table_stats')
    def test_request_stats_no_capabilities_for_table(self, *args):
        """Test request flow list."""
        (mock_request_table_stats_v0x4,
            mock_check_overlapping_multipart_request, _) = args
        mock_check_overlapping_multipart_request.return_value = False
        self.napp._request_stats(self.switch_v0x04)
        mock_request_table_stats_v0x4.return_value = 0xABC
        mock_request_table_stats_v0x4.assert_not_called()

    @patch('time.sleep', return_value=None)
    @patch('napps.kytos.of_core.v0x04.utils.update_flow_list')
    def test_on_handshake_completed_request_stats(self, *args):
        """Test request flow list."""
        (mock_update_flow_list_v0x04, _) = args
        mock_update_flow_list_v0x04.return_value = 0xABC
        sw = self._add_features_switch(self.switch_v0x04)
        self.napp.handle_handshake_completed_request_stats(sw)
        mock_update_flow_list_v0x04.assert_called_with(self.napp.controller,
                                                       self.switch_v0x04)

    @patch('napps.kytos.of_core.v0x04.utils.send_set_config')
    @patch('napps.kytos.of_core.v0x04.utils.send_desc_request')
    @patch('napps.kytos.of_core.v0x04.utils.handle_features_reply')
    def test_handle_features_reply(self, *args):
        """Test handle features reply."""
        (mock_freply_v0x04, mock_send_desc_request_v0x04,
         mock_send_set_config_v0x04) = args
        mock_buffers_put = MagicMock()
        self.napp.controller._buffers.app.put = mock_buffers_put
        dpid = self.switch_v0x04.connection.switch.dpid
        self.switch_v0x04.connection.switch.id = dpid
        mock_freply_v0x04.return_value = self.switch_v0x04.connection.switch
        name = 'kytos/of_core.v0x04.messages.in.ofpt_features_reply'
        self.switch_v0x04.connection.state = ConnectionState.SETUP
        self.switch_v0x04.connection.protocol.state = 'waiting_features_reply'
        content = {"source": self.switch_v0x04.connection}
        event = get_kytos_event_mock(name=name, content=content)
        count = self.switch_v0x04.connection.switch.update_lastseen.call_count
        assert count == 0

        # To simulate a few existing multipart replies for extra test cov
        self.napp._multipart_replies_xids[dpid] = {"flows": 2, "ports": 3}
        self.napp._multipart_replies_flows[dpid] = [MagicMock()]
        self.napp._multipart_replies_ports[dpid] = [MagicMock()]
        self.napp._multipart_replies_tables[dpid] = [MagicMock()]

        self.napp.handle_features_reply(event)
        count = self.switch_v0x04.connection.switch.update_lastseen.call_count
        assert count == 1
        mock_freply_v0x04.assert_called_with(self.napp.controller, event)
        mock_send_desc_request_v0x04.assert_called_with(
            self.napp.controller, self.switch_v0x04.connection.switch)
        mock_send_set_config_v0x04.assert_called_with(
            self.napp.controller, self.switch_v0x04.connection.switch)

        # Make sure it was cleaned up when handling features reply
        assert dpid not in self.napp._multipart_replies_xids
        assert dpid not in self.napp._multipart_replies_flows
        assert dpid not in self.napp._multipart_replies_ports
        assert dpid not in self.napp._multipart_replies_tables

        mock_buffers_put.assert_called()

    def test_update_switch_flows(self):
        """Test update_switch_flows."""
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_switch.id = dpid
        self.napp._multipart_replies_flows = {dpid: mock_switch}
        self.napp._multipart_replies_xids = {dpid: {'flows': 0xABC}}
        self.napp._update_switch_flows(mock_switch)
        assert self.napp._multipart_replies_xids == {dpid: {}}
        assert not self.napp._multipart_replies_flows

    def test_is_multipart_reply_ours(self):
        """Test _is_multipart_reply_ours."""
        dpid_a = '00:00:00:00:00:00:00:01'
        dpid_b = '00:00:00:00:00:00:00:02'
        mock_switch = get_switch_mock(dpid_a)
        mock_reply = MagicMock()
        mock_reply.header.xid = mock_switch
        type(mock_switch).id = PropertyMock(side_effect=[dpid_a,
                                                         dpid_a, dpid_b])
        self.napp._multipart_replies_xids = {dpid_a: {'flows': mock_switch}}
        response = self.napp._is_multipart_reply_ours(
            mock_reply, mock_switch, 'flows')
        assert response

        response = self.napp._is_multipart_reply_ours(
            mock_reply, mock_switch, 'flows')
        assert not response

    @patch('napps.kytos.of_core.main.Main.update_port_status')
    @patch('napps.kytos.of_core.main.Main.update_links')
    def test_emit_message_in(self, *args):
        """Test emit_message_in."""
        (mock_update_links, mock_update_port_status) = args

        mock_port_connection = MagicMock()
        msg_port_mock = MagicMock()
        msg_port_mock.header.message_type.name = 'ofpt_port_status'
        mock_port_connection.side_effect = True
        self.napp.emit_message_in(mock_port_connection,
                                  msg_port_mock)
        mock_update_port_status.assert_called_with(msg_port_mock,
                                                   mock_port_connection)

        mock_packet_in_connection = MagicMock()
        msg_packet_in_mock = MagicMock()
        mock_packet_in_connection.side_effect = True
        msg_packet_in_mock.header.message_type.name = 'ofpt_packet_in'
        self.napp.emit_message_in(mock_packet_in_connection,
                                  msg_packet_in_mock)
        mock_update_links.assert_called_with(msg_packet_in_mock,
                                             mock_packet_in_connection)

    @patch('napps.kytos.of_core.main.emit_message_out')
    def test_emit_message_out(self, mock_emit_message_out):
        """Test emit message_out."""
        mock_connection = MagicMock()
        mock_message = MagicMock()
        mock_connection.is_alive.return_value = True
        self.napp.emit_message_out(mock_connection, mock_message)
        mock_emit_message_out.assert_called()

    @patch('pyof.utils.v0x04.symmetric.echo_reply.EchoReply')
    @patch('napps.kytos.of_core.main.Main.emit_message_out')
    def test_handle_echo_request(self, *args):
        """Test handle echo request messages."""
        (mock_emit_message_out, mock_echo_reply) = args
        mock_event = MagicMock()
        mock_echo_request = MagicMock()
        mock_echo_reply.return_value = "A"
        mock_echo_request.header.xid = "A"
        mock_echo_request.data = "A"
        mock_event.source.protocol.version = 4
        mock_event.message = mock_echo_request
        self.napp.handle_echo_request(mock_event)
        mock_echo_reply.assert_called_with(xid=mock_echo_request.header.xid,
                                           data=mock_echo_request.data)
        mock_emit_message_out.assert_called_with(mock_event.source, "A")

    def test_handle_features_request_sent(self):
        """Test tests_handle_features_request_sent."""
        mock_protocol = MagicMock()
        mock_protocol.protocol.state = 'sending_features'
        expected = 'waiting_features_reply'
        name = 'kytos/of_core.v0x04.messages.out.ofpt_features_request'
        content = {'destination': mock_protocol}
        mock_event = get_kytos_event_mock(name=name, content=content)
        self.napp.handle_features_request_sent(mock_event)
        assert mock_event.destination.protocol.state == expected

    def test_handle_openflow_in_hello_failed(self):
        """Test handle_openflow_in_hello_failed."""
        mock_destination = MagicMock()
        content = {'destination': mock_destination}
        mock_event = get_kytos_event_mock(name='kytos/of_core',
                                          content=content)
        self.napp.handle_openflow_in_hello_failed(mock_event)
        assert mock_event.destination.close.call_count == 1

    @patch('napps.kytos.of_core.main.log')
    def test_shutdown(self, mock_log):
        """Test shutdown."""
        self.napp.shutdown()
        assert mock_log.debug.call_count == 1

    @patch('napps.kytos.of_core.main.Ethernet')
    def test_update_links(self, mock_ethernet):
        """Test update_links."""
        mock_buffer_put = MagicMock()
        self.napp.controller._buffers.app.put = mock_buffer_put
        ethernet = create_autospec(Ethernet)
        ethernet.ether_type = "A"
        mock_ethernet.side_effect = ethernet
        mock_message = MagicMock()
        mock_s = MagicMock()
        mock_s.switch.get_interface_by_port_no.side_effect = [AttributeError(),
                                                              True]
        self.napp.update_links(mock_message, mock_s)
        mock_ethernet.assert_called()
        mock_buffer_put.assert_called()

    def test_send_specific_port_mod(self):
        """Test send specific port."""
        mock_buffer_put = MagicMock()
        self.napp.controller._buffers.app.put = mock_buffer_put
        mock_port = MagicMock()
        mock_interface = MagicMock()
        type(mock_port.state).value = PropertyMock(side_effect=[0, 1, 2])
        current_state = 0
        self.napp._send_specific_port_mod(mock_port,
                                          mock_interface, current_state)
        mock_buffer_put.assert_called()

        current_state = 1
        self.napp._send_specific_port_mod(mock_port,
                                          mock_interface, current_state)
        mock_buffer_put.assert_called()

        current_state = 2
        self.napp._send_specific_port_mod(mock_port,
                                          mock_interface, current_state)
        mock_buffer_put.assert_called()

    @patch('napps.kytos.of_core.main.Interface')
    @patch('napps.kytos.of_core.main.Main._send_specific_port_mod')
    def test_update_port_status(self, *args):
        """Test update_port_status."""
        (mock_port_mod, mock_interface) = args
        mock_buffer_put = MagicMock()
        self.napp.controller._buffers.app.put = mock_buffer_put
        mock_intf = MagicMock()
        mock_interface.return_value = mock_intf
        mock_port_status = MagicMock()
        mock_source = MagicMock()
        mock_port = MagicMock()
        mock_port.state.value = PortState.OFPPS_LIVE
        speed = 10000000
        mock_port.curr_speed.value = speed

        mock_port_status.reason.value.side_effect = [0, 1, 2]
        mock_port_status.reason.enum_ref(0).name = 'OFPPR_ADD'
        mock_port_status.desc = mock_port
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_interface.assert_called()
        assert mock_intf.activate.call_count == 1
        assert mock_interface.call_args[1]["speed"] == speed

        # check OFPRR_MODIFY
        mock_port_status.reason.enum_ref(1).name = 'OFPPR_MODIFY'
        mock_source.switch.get_interface_by_port_no.return_value = False
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_port_mod.assert_called()
        mock_buffer_put.assert_called()
        assert mock_intf.activate.call_count == 2
        assert mock_interface.call_args[1]["speed"] == speed

        mock_source.switch.get_interface_by_port_no.return_value = mock_intf
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_intf.set_custom_speed.assert_called_with(speed)
        mock_port_mod.assert_called()
        mock_buffer_put.assert_called()

        # check OFPRR_DELETE
        mock_intf = MagicMock()
        mock_source.switch.get_interface_by_port_no.return_value = mock_intf
        mock_port_status.reason.enum_ref(2).name = 'OFPPR_DELETE'
        self.napp.update_port_status(mock_port_status, mock_source)
        mock_port_mod.assert_called()
        mock_buffer_put.assert_called()
        mock_intf.deactivate.assert_called()
