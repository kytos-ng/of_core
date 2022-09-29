"""Tests for high-level Flow of OpenFlow 1.3."""
import unittest
from unittest.mock import MagicMock

from pyof.v0x04.controller2switch.flow_mod import FlowMod as OFFlow04

from kytos.core.switch import Switch
from napps.kytos.of_core.v0x04.flow import Flow as Flow04
from kytos.core import log


class TestFlow(unittest.TestCase):
    """Test OF flow abstraction."""
    SWITCH = Switch('dpid')
    EXPECTED = {'id': '07d6b5ca38ee1a8de22061c9eb79e12f',
                'switch': SWITCH.id,
                'table_id': 1,
                'match': {
                    'dl_src': '11:22:33:44:55:66'
                },
                'priority': 2,
                'idle_timeout': 3,
                'hard_timeout': 4,
                'cookie': 5,
                'cookie_mask': 0,
                'instructions': [],
                'stats': {}}

    def test_flow_mod(self):
        """Convert a dict to flow and vice-versa."""
        with self.subTest(flow_class=Flow04):
            flow = Flow04.from_dict(self.EXPECTED, self.SWITCH)
            actual = flow.as_dict()
            self.assertDictEqual(self.EXPECTED, actual)

    def test_of_flow_mod(self):
        """Test convertion from Flow to OFFlow."""
        flow_mod_04 = Flow04.from_dict(self.EXPECTED, self.SWITCH)
        of_flow_mod_04 = flow_mod_04.as_of_delete_flow_mod()
        self.assertIsInstance(of_flow_mod_04, OFFlow04)
