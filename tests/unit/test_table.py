"""Tests for Tables"""
import pytest

from kytos.lib.helpers import get_switch_mock
from napps.kytos.of_core.table import TableStats


class TestTableStats():
    """Test TableStats Class."""

    @pytest.mark.parametrize(
        "table_dict",
        [
            (
                {
                    'switch': "00:00:00:00:00:00:00:01",
                    'table_id': 1,
                    'active_count': 0,
                    'lookup_count': 0,
                    'matched_count': 0,
                }
            ),
        ],
    )
    def test__eq__success_with_equal(self, table_dict):
        """Test success case to __eq__ override with equal tables."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        table_1 = TableStats.from_dict(table_dict, mock_switch)
        table_2 = TableStats.from_dict(table_dict, mock_switch)
        assert table_1 == table_2

    @pytest.mark.parametrize(
        "table_dict1, table_dict2",
        [
            (
                {
                    'switch': "00:00:00:00:00:00:00:01",
                    'table_id': 1,
                    'active_count': 0,
                    'lookup_count': 0,
                    'matched_count': 0
                },
                {
                    'switch': "00:00:00:00:00:00:00:01",
                    'table_id': 2,
                    'active_count': 1,
                    'lookup_count': 2,
                    'matched_count': 3
                }
            ),
        ],
    )
    def test__eq__success_different_tables(self, table_dict1, table_dict2):
        """Test success case to __eq__ override with different tables."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        table_1 = TableStats.from_dict(table_dict1, mock_switch)
        table_2 = TableStats.from_dict(table_dict2, mock_switch)
        assert table_1 != table_2

    @pytest.mark.parametrize(
        "table_dict",
        [
            (
                {
                    'switch': "00:00:00:00:00:00:00:01",
                    'table_id': 1,
                    'active_count': 0,
                    'lookup_count': 0,
                    'matched_count': 0,
                }
            ),
        ],
    )
    def test__eq__fail(self, table_dict):
        """Test the case where __eq__ receives objects with different types."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        table_1 = TableStats.from_dict(table_dict, mock_switch)
        table_2 = "string_object"
        with pytest.raises(ValueError):
            return table_1 == table_2
