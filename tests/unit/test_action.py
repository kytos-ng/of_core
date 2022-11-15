"""Test Action abstraction for v0x04."""
from unittest.mock import MagicMock

import pytest
from pyof.foundation.basic_types import UBInt32

from napps.kytos.of_core.v0x04.flow import Action as Action04

# pylint: disable=protected-access,unnecessary-lambda-assignment


@pytest.mark.parametrize(
    'action_class, action_dict', [
        [
            Action04,
            {
                'action_type': 'output',
                'port': UBInt32(1),
            },
        ],
        [
            Action04,
            {
                'action_type': 'set_queue',
                'queue_id': UBInt32(4),
            }
        ],
        [
            Action04,
            {
                'action_type': 'pop_vlan',
            }
        ],
        [
            Action04,
            {
                'action_type': 'push_vlan',
                'tag_type': 'c',
            }
        ],
        [
            Action04,
            {
                'action_type': 'push_vlan',
                'tag_type': 's',
            }
        ],
    ]
)
def test_all_actions(action_class, action_dict):
    """Test all action fields from and to dict."""
    action = action_class.from_dict(action_dict)
    actual = action.as_dict()
    of_action = action.as_of_action()
    assert action_dict == actual
    assert action_dict == action_class.from_of_action(of_action).as_dict()


def test_add_action_class():
    """Test add_action_class."""
    name, new_class = "some_class", MagicMock()
    Action04.add_action_class(name, new_class)
    assert Action04._action_class[name] == new_class


def test_add_experimenter_classes():
    """Test add_experimenter_classes."""
    resp = MagicMock()
    experimenter, func = 0xff000002, lambda body: resp
    Action04.add_experimenter_classes(experimenter, func)
    assert Action04._experimenter_classes[experimenter] == func
    assert Action04.get_experimenter_class(experimenter, b'\xff') == resp
