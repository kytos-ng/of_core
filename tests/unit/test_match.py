"""Test Match abstraction for v0x01 and v0x04."""
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, patch

from napps.kytos.of_core.v0x01.flow import Match as Match01
from napps.kytos.of_core.v0x04.flow import Match as Match04


class TestMatch(TestCase):
    """Tests for the Match class."""

    EXPECTED = {
        'in_port': 1,
        'dl_src': '11:22:33:44:55:66',
        'dl_dst': 'aa:bb:cc:dd:ee:ff',
        'dl_vlan': 2,
        'dl_vlan_pcp': 3,
        'dl_type': 4,
        'nw_proto': 5,
        'nw_src': '1.2.3.4/31',
        'nw_dst': '5.6.7.0/24',
        'tp_src': 6,
        'tp_dst': 7,
    }

    EXPECTED_OF_13 = {
        'in_phy_port': 2,
        'ip_dscp': 1,
        'ip_ecn': 3,
        'udp_src': 4,
        'udp_dst': 5,
        'sctp_src': 6,
        'sctp_dst': 7,
        'icmpv4_type': 8,
        'icmpv4_code': 9,
        'ipv6_src': 'abcd:0000:0000:0000:0000:0000:0000:0001/64',
        'ipv6_dst': 'ef01:0000:0000:0000:0000:0000:0000:0002/48',
        'ipv6_flabel': 27,
        'icmpv6_type': 5,
        'icmpv6_code': 6,
        'nd_tar': 1234567,
        'nd_sll': 345,
        'nd_tll': 543,
        'v6_hdr': 45,
        'arp_op': 10,
        'arp_spa': '4.5.6.7/30',
        'arp_tpa': '8.9.10.11/29',
        'arp_sha': '11:22:33:44:55:66',
        'arp_tha': 'aa:bb:cc:dd:ee:ff',
        'mpls_lab': 11,
        'mpls_tc': 4,
        'mpls_bos': 5,
        'pbb_isid': 45,
        'metadata': 4567,
        'tun_id': 6789,
    }
    EXPECTED_OF_13.update(EXPECTED)

    def test_all_fields(self):
        """Test all match fields from and to dict."""
        for match_class in Match01, Match04:
            with self.subTest(match_class=match_class):
                match = match_class.from_dict(self.EXPECTED)
                actual = match.as_dict()
                self.assertDictEqual(self.EXPECTED, actual)

    @patch('napps.kytos.of_core.v0x04.flow.MatchFieldFactory')
    def test_from_of_match(self, mock_factory):
        """Test from_of_match."""
        mock_match = MagicMock()
        mock_field = MagicMock()
        mock_tlv = MagicMock()
        mock_field.name = 'A'
        mock_field.value = 42
        mock_factory.from_of_tlv.return_value = mock_field
        type(mock_match).oxm_match_fields = (PropertyMock(
                                             return_value=[[mock_tlv]]))
        response = Match04.from_of_match(mock_match)
        self.assertEqual(mock_factory.from_of_tlv.call_count, 1)
        self.assertIsInstance(response, Match04)

    def test_match_tlv(self):
        """Test OF 1.3 matches"""
        match = Match04.from_dict(self.EXPECTED_OF_13)
        self.assertDictEqual(
            Match04.from_of_match(match.as_of_match()).as_dict(),
            self.EXPECTED_OF_13
        )

    def test_match01_as_dict(self) -> None:
        """Test match01 as_dict."""
        match_values = {'in_port': 1, 'dl_vlan': 2}
        match_01 = Match01(**match_values)
        assert len(match_01.as_dict()) == len(match_values)
