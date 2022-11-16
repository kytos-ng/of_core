"""Deal with OpenFlow 1.3 specificities related to flows."""
from itertools import chain
from typing import Callable, Optional, Type

from pyof.foundation.network_types import EtherType
from pyof.v0x04.common.action import ActionExperimenter
from pyof.v0x04.common.action import ActionOutput as OFActionOutput
from pyof.v0x04.common.action import ActionPopVLAN as OFActionPopVLAN
from pyof.v0x04.common.action import ActionPush as OFActionPush
from pyof.v0x04.common.action import ActionSetField as OFActionSetField
from pyof.v0x04.common.action import ActionSetQueue as OFActionSetQueue
from pyof.v0x04.common.action import ActionType
from pyof.v0x04.common.flow_instructions import \
    InstructionApplyAction as OFInstructionApplyAction
from pyof.v0x04.common.flow_instructions import \
    InstructionClearAction as OFInstructionClearAction
from pyof.v0x04.common.flow_instructions import \
    InstructionGotoTable as OFInstructionGotoTable
from pyof.v0x04.common.flow_instructions import \
    InstructionMeter as OFInstructionMeter
from pyof.v0x04.common.flow_instructions import InstructionType
from pyof.v0x04.common.flow_instructions import \
    InstructionWriteAction as OFInstructionWriteAction
from pyof.v0x04.common.flow_instructions import \
    InstructionWriteMetadata as OFInstructionWriteMetadata
from pyof.v0x04.common.flow_match import Match as OFMatch
from pyof.v0x04.common.flow_match import (OxmMatchFields, OxmOfbMatchField,
                                          OxmTLV, VlanId)
from pyof.v0x04.controller2switch.flow_mod import FlowMod

from napps.kytos.of_core.flow import (ActionBase, ActionFactoryBase, FlowBase,
                                      FlowStats, InstructionBase,
                                      InstructionFactoryBase, MatchBase,
                                      PortStats)
from napps.kytos.of_core.v0x04.match_fields import MatchFieldFactory

__all__ = ('ActionOutput', 'ActionSetVlan', 'ActionSetQueue', 'ActionPushVlan',
           'ActionPopVlan', 'Action', 'Flow', 'FlowStats', 'PortStats')


class Match(MatchBase):
    """High-level Match for OpenFlow 1.3 match fields."""

    @classmethod
    def from_of_match(cls, of_match):
        """Return an instance from a pyof Match."""
        match = cls()
        match_fields = (MatchFieldFactory.from_of_tlv(tlv)
                        for tlv in of_match.oxm_match_fields)
        for field in match_fields:
            if field is not None:
                setattr(match, field.name, field.value)
        return match

    def as_of_match(self):
        """Create an OF Match with TLVs from instance attributes."""
        oxm_fields = OxmMatchFields()
        for field_name, value in self.__dict__.items():
            if value is not None:
                field = MatchFieldFactory.from_name(field_name, value)
                if field:
                    tlv = field.as_of_tlv()
                    oxm_fields.append(tlv)
        return OFMatch(oxm_match_fields=oxm_fields)


class ActionOutput(ActionBase):
    """Action with an output port."""

    def __init__(self, port):
        """Require an output port.

        Args:
            port (int): Specific port number.
        """
        self.port = port
        self.action_type = 'output'

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high-level ActionOuput instance from pyof ActionOutput."""
        return cls(port=of_action.port.value)

    def as_of_action(self):
        """Return a pyof ActionOuput instance."""
        return OFActionOutput(port=self.port)


class ActionSetQueue(ActionBase):
    """Action to set a queue for the packet."""

    def __init__(self, queue_id):
        """Require the id of the queue.

        Args:
            queue_id (int): Queue ID.
        """
        self.queue_id = queue_id
        self.action_type = 'set_queue'

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high-level ActionSetQueue instance from pyof class."""
        return cls(queue_id=of_action.queue_id.value)

    def as_of_action(self):
        """Return a pyof ActionSetQueue instance."""
        return OFActionSetQueue(queue_id=self.queue_id)


class ActionPopVlan(ActionBase):
    """Action to pop the outermost VLAN tag."""

    def __init__(self, *args):  # pylint: disable=unused-argument
        """Initialize the action with the correct action_type."""
        self.action_type = 'pop_vlan'

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high-level ActionPopVlan instance from the pyof class."""
        return cls()

    def as_of_action(self):
        """Return a pyof ActionPopVLAN instance."""
        return OFActionPopVLAN()


class ActionPushVlan(ActionBase):
    """Action to push a VLAN tag."""

    def __init__(self, tag_type):
        """Require a tag_type for the VLAN."""
        self.action_type = 'push_vlan'
        self.tag_type = tag_type

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high level ActionPushVlan instance from pyof ActionPush."""
        if of_action.ethertype.value == EtherType.VLAN_QINQ:
            return cls(tag_type='s')
        return cls(tag_type='c')

    def as_of_action(self):
        """Return a pyof ActionPush instance."""
        if self.tag_type == 's':
            return OFActionPush(action_type=ActionType.OFPAT_PUSH_VLAN,
                                ethertype=EtherType.VLAN_QINQ)
        return OFActionPush(action_type=ActionType.OFPAT_PUSH_VLAN,
                            ethertype=EtherType.VLAN)


class ActionSetVlan(ActionBase):
    """Action to set VLAN ID."""

    def __init__(self, vlan_id):
        """Require a VLAN ID."""
        self.vlan_id = vlan_id
        self.action_type = 'set_vlan'

    @classmethod
    def from_of_action(cls, of_action):
        """Return high-level ActionSetVlan object from pyof ActionSetField."""
        vlan_id = int.from_bytes(of_action.field.oxm_value, 'big') & 4095
        return cls(vlan_id)

    def as_of_action(self):
        """Return a pyof ActionSetField instance."""
        tlv = OxmTLV()
        tlv.oxm_field = OxmOfbMatchField.OFPXMT_OFB_VLAN_VID
        oxm_value = self.vlan_id | VlanId.OFPVID_PRESENT
        tlv.oxm_value = oxm_value.to_bytes(2, 'big')
        return OFActionSetField(field=tlv)


class Action(ActionFactoryBase):
    """An action to be executed once a flow is activated.

    This class behavies like a factory but has no "Factory" suffix for end-user
    usability issues.
    """

    # Set v0x04 classes for action types and pyof classes
    _action_class = {
        'output': ActionOutput,
        'set_vlan': ActionSetVlan,
        'push_vlan': ActionPushVlan,
        'pop_vlan': ActionPopVlan,
        'set_queue': ActionSetQueue,
        OFActionOutput: ActionOutput,
        OFActionSetField: ActionSetVlan,
        OFActionPush: ActionPushVlan,
        OFActionPopVLAN: ActionPopVlan,
        OFActionSetQueue: ActionSetQueue
    }

    # experimenter int value to pyof classes to unpack from bytes
    _experimenter_classes = {}

    @classmethod
    def add_action_class(cls, class_name, new_class):
        """Add a new action.

        To be used by modules implementing Experimenter Actions.
        """
        cls._action_class[class_name] = new_class

    @classmethod
    def add_experimenter_classes(
        cls, experimenter: int,
        func: Callable[[bytes], Optional[Type[ActionExperimenter]]]
    ):
        """Add a callable that take bytes to map to Experimenter Actions."""
        cls._experimenter_classes[int(experimenter)] = func

    @classmethod
    def get_experimenter_class(cls, experimenter: int, body: bytes):
        """Get Experimenter class."""
        return cls._experimenter_classes[int(experimenter)](body)


class InstructionAction(InstructionBase):
    """Base class for instruction dealing with actions."""

    _action_factory = Action
    _instruction_type = None
    _of_instruction_class = None

    def __init__(self, actions=None):
        self.instruction_type = self._instruction_type
        self.actions = actions or []

    def as_dict(self):
        instruction_dict = {'instruction_type': self.instruction_type}
        instruction_dict['actions'] = [action.as_dict()
                                       for action in self.actions if action]
        return instruction_dict

    @classmethod
    def from_of_instruction(cls, of_instruction):
        """Create high-level Instruction from pyof Instruction."""
        actions = []
        for of_action in of_instruction.actions:
            klass = Action
            if isinstance(of_action, ActionExperimenter):
                klass = Action.get_experimenter_class(of_action.experimenter,
                                                      of_action.body.pack())
            actions.append(klass.from_of_action(of_action))
        return cls(actions)

    def as_of_instruction(self):
        """Return a pyof Instruction instance."""
        of_actions = [action.as_of_action() for action in self.actions]
        # Disable not-callable error as subclasses will set a class
        # pylint: disable=not-callable
        return self._of_instruction_class(of_actions)


class InstructionApplyAction(InstructionAction):
    """Instruct switch to apply the actions."""

    _instruction_type = 'apply_actions'
    _of_instruction_class = OFInstructionApplyAction


class InstructionClearAction(InstructionAction):
    """Instruct switch to clear the actions."""

    _instruction_type = 'clear_actions'
    _of_instruction_class = OFInstructionClearAction


class InstructionWriteAction(InstructionAction):
    """Instruct switch to write the actions."""

    _instruction_type = 'write_actions'
    _of_instruction_class = OFInstructionWriteAction


class InstructionGotoTable(InstructionBase):
    """Instruct the switch to move to another table."""

    def __init__(self, table_id=0):
        self.instruction_type = 'goto_table'
        self.table_id = table_id

    @classmethod
    def from_of_instruction(cls, of_instruction):
        """Create high-level Instruction from pyof Instruction."""
        return cls(table_id=of_instruction.table_id.value)

    def as_of_instruction(self):
        """Return a pyof Instruction instance."""
        return OFInstructionGotoTable(self.table_id)


class InstructionMeter(InstructionBase):
    """Instruct the switch to apply a meter."""

    def __init__(self, meter_id=0):
        self.instruction_type = 'meter'
        self.meter_id = meter_id

    @classmethod
    def from_of_instruction(cls, of_instruction):
        """Create high-level Instruction from pyof Instruction."""
        return cls(meter_id=of_instruction.meter_id.value)

    def as_of_instruction(self):
        """Return a pyof Instruction instance."""
        return OFInstructionMeter(self.meter_id)


class InstructionWriteMetadata(InstructionBase):
    """Instruct the switch to write metadata."""

    def __init__(self, metadata=0, metadata_mask=0):
        self.instruction_type = 'write_metadata'
        self.metadata = metadata
        self.metadata_mask = metadata_mask

    @classmethod
    def from_of_instruction(cls, of_instruction):
        """Create high-level Instruction from pyof Instruction."""
        return cls(metadata=of_instruction.metadata.value,
                   metadata_mask=of_instruction.metadata_mask.value)

    def as_of_instruction(self):
        """Return a pyof Instruction instance."""
        return OFInstructionWriteMetadata(self.metadata, self.metadata_mask)


class Instruction(InstructionFactoryBase):
    """An instruction the flow executes."""

    _instruction_class = {
        'apply_actions': InstructionApplyAction,
        OFInstructionApplyAction: InstructionApplyAction,
        'clear_actions': InstructionClearAction,
        OFInstructionClearAction: InstructionClearAction,
        'goto_table': InstructionGotoTable,
        OFInstructionGotoTable: InstructionGotoTable,
        'meter': InstructionMeter,
        OFInstructionMeter: InstructionMeter,
        'write_actions': InstructionWriteAction,
        OFInstructionWriteAction: InstructionWriteAction,
        'write_metadata': InstructionWriteMetadata,
        OFInstructionWriteMetadata: InstructionWriteMetadata
    }


class Flow(FlowBase):
    """High-level flow representation for OpenFlow 1.0.

    This is a subclass that only deals with 1.3 flow actions.
    """

    _action_factory = Action
    _flow_mod_class = FlowMod
    _match_class = Match

    def __init__(self, *args, **kwargs):
        """Require a cookie mask."""
        cookie_mask = kwargs.pop('cookie_mask', 0)
        instructions = kwargs.pop('instructions', None)
        super().__init__(*args, **kwargs)
        self.cookie_mask = cookie_mask
        self.instructions = instructions or []

    def as_dict(self, include_id=True):
        """Return a representation of a Flow as a dictionary."""
        flow_dict = super().as_dict(include_id=include_id)
        flow_dict['cookie_mask'] = self.cookie_mask
        flow_dict['instructions'] = [instruction.as_dict() for
                                     instruction in self.instructions]
        return flow_dict

    @classmethod
    def from_dict(cls, flow_dict, switch):
        """Create a Flow instance from a dictionary."""
        flow = super().from_dict(flow_dict, switch)
        flow.instructions = []
        if 'actions' in flow_dict and flow_dict['actions']:
            instruction_apply_actions = InstructionApplyAction()
            for action_dict in flow_dict['actions']:
                action = cls._action_factory.from_dict(action_dict)
                if action:
                    instruction_apply_actions.actions.append(action)
            flow.instructions.append(instruction_apply_actions)
        if 'instructions' in flow_dict:
            for instruction_dict in flow_dict['instructions']:
                instruction = Instruction.from_dict(instruction_dict)
                if instruction:
                    flow.instructions.append(instruction)
        return flow

    @staticmethod
    def _get_of_actions(of_flow_stats):
        """Return the pyof actions from pyof ``FlowStats.instructions``."""
        # Add list of high-level actions
        # Filter action instructions
        apply_actions = InstructionType.OFPIT_APPLY_ACTIONS
        of_instructions = (ins for ins in of_flow_stats.instructions
                           if ins.instruction_type == apply_actions)
        # Get actions from a list of actions
        return chain.from_iterable(ins.actions for ins in of_instructions)

    def _as_of_flow_mod(self, command):
        """Return pyof FlowMod with a ``command`` to add or delete a flow.

        Actions become items of the ``instructions`` attribute.
        """
        of_flow_mod = super()._as_of_flow_mod(command)
        of_flow_mod.cookie_mask = self.cookie_mask
        of_flow_mod.instructions = [instruction.as_of_instruction() for
                                    instruction in self.instructions]
        return of_flow_mod

    @classmethod
    def from_of_flow_stats(cls, of_flow_stats, switch):
        """Create a flow with latest stats based on pyof FlowStats."""
        instructions = [Instruction.from_of_instruction(of_instruction)
                        for of_instruction in of_flow_stats.instructions]
        flow = super().from_of_flow_stats(of_flow_stats, switch)
        flow.instructions = instructions
        return flow
