"""Test Action abstraction for v0x04."""
import pytest
from pyof.foundation.basic_types import UBInt32

from napps.kytos.of_core.v0x04.flow import Action as Action04


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
