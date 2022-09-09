"""Test v0x04.utils methods."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from kytos.lib.helpers import (get_connection_mock, get_controller_mock,
                               get_switch_mock)
from napps.kytos.of_core.v0x04.utils import (handle_features_reply,
                                             handle_port_desc, say_hello,
                                             send_desc_request, send_echo,
                                             send_port_request,
                                             send_set_config)


@patch('napps.kytos.of_core.v0x04.utils.aemit_message_out')
async def test_say_hello(mock_aemit_message_out, controller, switch_one):
    """Test say_hello."""
    await say_hello(controller, switch_one)
    mock_aemit_message_out.assert_called()


@patch('kytos.core.buffers.KytosEventBuffer.aput')
async def test_handle_port_desc(mock_event_buffer, controller, switch_one):
    """Test Handle Port Desc."""
    mock_port = MagicMock()
    await handle_port_desc(controller, switch_one, [mock_port])
    assert switch_one.update_or_create_interface.call_count == 1
    mock_event_buffer.assert_called()
    assert controller.buffers.app.aput.call_count == 3


class TestUtils(TestCase):
    """Test utils."""

    def setUp(self):
        """Execute steps before each tests."""
        self.mock_controller = get_controller_mock()
        self.mock_switch = get_switch_mock('00:00:00:00:00:00:00:01', 0x04)
        self.mock_connection = get_connection_mock(0x04, self.mock_switch)

    @patch('napps.kytos.of_core.v0x04.utils.emit_message_out')
    def test_send_desc_request(self, mock_emit_message_out):
        """Test send_desc_request."""
        send_desc_request(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    @patch('napps.kytos.of_core.v0x04.utils.emit_message_out')
    def test_port_request(self, mock_emit_message_out):
        """Test send_desc_request."""
        send_port_request(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    def test_handle_features_reply(self):
        """Test Handle features reply."""
        mock_controller = MagicMock()
        mock_event = MagicMock()
        mock_controller.get_switch_or_create.return_value = self.mock_switch
        response = handle_features_reply(mock_controller, mock_event)
        self.assertEqual(self.mock_switch, response)
        self.assertEqual(self.mock_switch.update_features.call_count, 1)

    @patch('napps.kytos.of_core.v0x04.utils.emit_message_out')
    def test_send_echo(self, mock_emit_message_out):
        """Test send_echo."""
        send_echo(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    @patch('napps.kytos.of_core.v0x04.utils.emit_message_out')
    def test_set_config(self, mock_emit_message_out):
        """Test set_config."""
        send_set_config(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()
