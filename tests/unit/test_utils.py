"""Test utils methods."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pyof.v0x04.common.header import Type

from kytos.lib.helpers import (get_connection_mock, get_controller_mock,
                               get_switch_mock)
from napps.kytos.of_core.msg_prios import of_msg_prio
from napps.kytos.of_core.utils import (GenericHello, _emit_message,
                                       _unpack_int, aemit_message_in,
                                       aemit_message_out, emit_message_in,
                                       emit_message_out, of_slicer)


@patch('kytos.core.buffers.KytosEventBuffer.aput')
async def test_aemit_message_in(controller, switch_one):
    """Test aemit_message_in."""
    mock_message = MagicMock()
    mock_message.header.message_type.value = Type.OFPT_FLOW_MOD.value
    await aemit_message_in(controller, switch_one.connection, mock_message)
    assert controller.buffers.msg_in.aput.call_count == 1
    kytos_event = controller.buffers.msg_in.aput.call_args[0][0]
    assert kytos_event.priority == of_msg_prio(Type.OFPT_FLOW_MOD.value)


@patch('kytos.core.buffers.KytosEventBuffer.aput')
async def test_aemit_message_out(controller, switch_one):
    """Test aemit_message_in."""
    mock_message = MagicMock()
    mock_message.header.message_type.value = Type.OFPT_FLOW_MOD.value
    await aemit_message_out(controller, switch_one.connection, mock_message)
    assert controller.buffers.msg_out.aput.call_count == 1
    kytos_event = controller.buffers.msg_out.aput.call_args[0][0]
    assert kytos_event.priority == of_msg_prio(Type.OFPT_FLOW_MOD.value)


class TestUtils(TestCase):
    """Test utils."""

    def setUp(self):
        """Execute steps before each tests."""
        self.mock_controller = get_controller_mock()
        self.mock_switch = get_switch_mock('00:00:00:00:00:00:00:01', 0x04)
        self.mock_connection = get_connection_mock(0x04, self.mock_switch)

    def test_of_slicer(self):
        """Test of_slicer."""
        data = b'\x04\x00\x00\x10\x00\x00\x00\x3e'
        data += b'\x00\x01\x00\x08\x00\x00\x00\x10'
        response = of_slicer(data)
        self.assertEqual(data, response[0][0])
        self.assertCountEqual(response[1], [])

    def test_of_slicer2(self):
        """Test of_slicer with insufficient bytes."""
        data = b'\x04\x00\x00'
        response = of_slicer(data)
        self.assertCountEqual(response[0], [])
        self.assertEqual(response[1], data)

    def test_of_slicer_invalid_data1(self):
        """Test of_slicer with invalid data: oflen is zero"""
        data = b'\x04\x00\x00\x00'
        response = of_slicer(data)
        self.assertCountEqual(response[0], [])
        self.assertCountEqual(response[1], [])
        data = b'\x04\x00\x00\x05\x99\x04\x00\x00\x00'
        response = of_slicer(data)
        self.assertEqual(response[0][0], data[:5])
        self.assertCountEqual(response[1], [])

    def test_of_slicer_invalid_data2(self):
        """Test of_slicer with invalid data: non openflow"""
        data = b'\x00\x00\x00\x00'
        response = of_slicer(data)
        self.assertCountEqual(response[0], [])
        self.assertCountEqual(response[1], [])
        data = b'\x04\x00\x00\x00\x00\x00\x00\x00'
        response = of_slicer(data)
        self.assertCountEqual(response[0], [])
        self.assertCountEqual(response[1], [])

    def test_unpack_int(self):
        """Test test_unpack_int."""
        mock_packet = MagicMock()
        response = _unpack_int(mock_packet)
        self.assertEqual(int.from_bytes(mock_packet,
                                        byteorder='big'), response)

    @patch('napps.kytos.of_core.utils.KytosEvent')
    def test_emit_message(self, mock_event):
        """Test emit_message."""
        mock_message = MagicMock()
        _emit_message(self.mock_controller, self.mock_connection, mock_message,
                      'in')
        mock_event.assert_called()

        _emit_message(self.mock_controller, self.mock_connection, mock_message,
                      'out')
        mock_event.assert_called()

    @patch('napps.kytos.of_core.utils._emit_message')
    def test_emit_message_in_out(self, mock_message_in):
        """Test emit_message in and out."""

        emit_message_in(self.mock_controller, self.mock_connection, 'in')
        mock_message_in.assert_called()

        emit_message_out(self.mock_controller, self.mock_connection, 'in')
        mock_message_in.assert_called()


class TestGenericHello(TestCase):
    """Test GenericHello."""

    data = b'\x04\x00\x00\x10\x00\x00\x00\x00\x00\x01\x00\x08\x00\x00\x00\x10'

    @patch('napps.kytos.of_core.utils.OFPTYPE')
    def test_pack(self, mock_ofptype):
        """Test pack."""
        mock_ofptype.return_value = True
        generic = GenericHello(packet=self.data, versions=b'\x04')
        response = generic.pack()
        self.assertEqual(self.data, response)
