"""Test Action abstraction for v0x01 and v0x04."""
import unittest

from napps.kytos.of_core.v0x01.flow import Action as Action01
from napps.kytos.of_core.v0x04.flow import Action as Action04
from pyof.foundation.basic_types import UBInt16, UBInt32


class TestAction(unittest.TestCase):
    """Tests for the Action class."""

    def test_all_actions(self):
        """Test all action fields from and to dict."""
        action_dicts = [
            {
                'tests': [Action01, Action04],
                'action': {
                    'action_type': 'output',
                    'port': UBInt32(1),
                },
            },
            {
                'tests': [Action01, Action04],
                'action': {
                    'action_type': 'set_vlan',
                    'vlan_id': UBInt16(2),
                },
            },
            {
                'tests': [Action04],
                'action': {
                    'action_type': 'set_queue',
                    'queue_id': UBInt32(4),
                }
            },
            {
                'tests': [Action04],
                'action': {
                    'action_type': 'pop_vlan',
                }
            },
            {
                'tests': [Action04],
                'action': {
                    'action_type': 'push_vlan',
                    'tag_type': 'c',
                }
            },                       
            {
                'tests': [Action04],
                'action': {
                    'action_type': 'push_vlan',
                    'tag_type': 's',
                }
            }, 
        ]
        for action_class in Action01, Action04:
            with self.subTest(action_class=action_class):
                for action_test in action_dicts:
                    if action_class not in action_test['tests']:
                        continue
                    expected = action_test['action']
                    with self.subTest(expected=expected):
                        action = action_class.from_dict(expected)
                        actual = action.as_dict()
                        of_action = action.as_of_action()
                        self.assertDictEqual(expected, actual)
                        self.assertDictEqual(
                            expected,
                            action_class.from_of_action(of_action).as_dict()
                        )
