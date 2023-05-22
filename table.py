"""High-level abstraction for Tables of multiple OpenFlow versions.
"""
import json


class TableStats:
    """Class with table fields.
    """

    def __init__(self, switch, table_id=0x0, active_count=0,
                 lookup_count=0, matched_count=0):
        """Assign parameters to attributes.

        Args:
            switch (kytos.core.switch.Switch): Switch ID is used to uniquely
                identify a flow.
            table_id (int): The index of a single table or 0xff for all tables.
            active_count: Number of active entries.
            lookup_count: Number of packets looked up in table.
            matched_count: Number of packets that hit table.
        """
        self.switch = switch
        self.table_id = table_id
        self.active_count = active_count
        self.lookup_count = lookup_count
        self.matched_count = matched_count

    def as_dict(self):
        """Return the Table as a serializable Python dictionary.
        """
        table_dict = {
            'switch': self.switch.id,
            'table_id': self.table_id,
            'active_count': self.active_count,
            'lookup_count': self.lookup_count,
            'matched_count': self.matched_count
        }

        return table_dict

    @classmethod
    def from_dict(cls, table_dict, switch):
        """Return an instance with values from ``table_dict``."""
        table = cls(switch)

        for attr_name, attr_value in table_dict.items():
            if attr_name in vars(table):
                setattr(table, attr_name, attr_value)

        table.switch = switch
        return table

    def as_json(self, sort_keys=False):
        """Return the representation of a flow in JSON format.

        Args:
            sort_keys (bool): ``False`` by default (Python's default).
        Returns:
            string: Flow JSON string representation.

        """
        return json.dumps(self.as_dict(), sort_keys=sort_keys)

    @classmethod
    def from_of_table_stats(cls, of_table_stats, switch):
        """Create a flow with latest stats based on pyof FlowStats."""
        return cls(switch,
                   table_id=of_table_stats.table_id.value,
                   active_count=of_table_stats.active_count.value,
                   lookup_count=of_table_stats.lookup_count.value,
                   matched_count=of_table_stats.matched_count.value)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise ValueError(f'Error comparing tables: {other} is not '
                             f'an instance of {self.__class__}')

        return self.as_dict() == other.as_dict()
