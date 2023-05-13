"""Tests for high-level Flow of OpenFlow 1.3."""
from unittest import TestCase

from kytos.lib.helpers import get_switch_mock
from napps.kytos.of_core.table import TableStats


class TestTableStats(TestCase):
    """Test TableStats Class."""

    def test__eq__success_with_equal(self):
        """Test success case to __eq__ override with equal tables."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        table_dict = {
                        'switch': mock_switch.id,
                        'table_id': 1,
                        'active_count': 0,
                        'lookup_count': 0,
                        'matched_count': 0
                     }

        with self.subTest(table_class=TableStats):
            table_1 = TableStats.from_dict(table_dict, mock_switch)
            table_2 = TableStats.from_dict(table_dict, mock_switch)
            self.assertEqual(table_1 == table_2, True)

    def test__eq__success_with_different_tables(self):
        """Test success case to __eq__ override with different tables."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        table_dict_1 = {
                            'switch': mock_switch.id,
                            'table_id': 1,
                            'active_count': 0,
                            'lookup_count': 0,
                            'matched_count': 0
                       }

        table_dict_2 = {
                            'switch': mock_switch.id,
                            'table_id': 2,
                            'active_count': 1,
                            'lookup_count': 2,
                            'matched_count': 3
                       }

        with self.subTest(table_class=TableStats):
            table_1 = TableStats.from_dict(table_dict_1, mock_switch)
            table_2 = TableStats.from_dict(table_dict_2, mock_switch)
            self.assertEqual(table_1 == table_2, False)

    def test__eq__fail(self):
        """Test the case where __eq__ receives objects with different types."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        table_dict = {
                        'switch': mock_switch.id,
                        'table_id': 1,
                        'active_count': 0,
                        'lookup_count': 0,
                        'matched_count': 0
                     }

        with self.subTest(table_class=TableStats):
            table_1 = TableStats.from_dict(table_dict, mock_switch)
            table_2 = "string_object"
            with self.assertRaises(ValueError):
                return table_1 == table_2
