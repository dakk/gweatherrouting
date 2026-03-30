# -*- coding: utf-8 -*-
# Copyright (C) 2017-2026 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""

import unittest
from unittest.mock import MagicMock, PropertyMock

from gweatherrouting.core.datasource import (
    AISDataPacket,
    DataPacket,
    DataSource,
    NMEADataPacket,
)


class TestNMEADataPacket(unittest.TestCase):
    def test_parse_rmc(self):
        sentence = "$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68"
        pkt = NMEADataPacket.parse(sentence)
        self.assertTrue(pkt.is_position())

    def test_parse_mwv(self):
        sentence = "$IIMWV,045.0,R,12.5,N,A*0A"
        pkt = NMEADataPacket.parse(sentence)
        self.assertFalse(pkt.is_position())
        self.assertEqual(pkt.data.sentence_type, "MWV")

    def test_serialize(self):
        sentence = "$IIMWV,045.0,R,12.5,N,A*0A"
        pkt = NMEADataPacket.parse(sentence)
        self.assertIn("MWV", pkt.serialize())


class TestAISDataPacket(unittest.TestCase):
    def test_creation(self):
        raw = "!AIVDM,1,1,,B,13u@Dt002s000000000000000000,0*59"
        pkt = AISDataPacket(raw)
        self.assertFalse(pkt.is_position())
        self.assertFalse(pkt.is_heading())

    def test_serialize(self):
        raw = "!AIVDM,1,1,,B,13u@Dt002s000000000000000000,0*59"
        pkt = AISDataPacket(raw)
        self.assertEqual(pkt.serialize(), raw)


class TestDataPacketIsPosition(unittest.TestCase):
    """Tests for DataPacket.is_position using mock sentences."""

    def test_is_position_true(self):
        mock_sentence = MagicMock()
        mock_sentence.__contains__ = lambda self, key: key in ("latitude", "longitude")
        pkt = DataPacket("test", mock_sentence)
        self.assertTrue(pkt.is_position())

    def test_is_position_false_no_latitude(self):
        mock_sentence = MagicMock()
        mock_sentence.__contains__ = lambda self, key: key == "longitude"
        pkt = DataPacket("test", mock_sentence)
        self.assertFalse(pkt.is_position())

    def test_is_position_false_no_longitude(self):
        mock_sentence = MagicMock()
        mock_sentence.__contains__ = lambda self, key: key == "latitude"
        pkt = DataPacket("test", mock_sentence)
        self.assertFalse(pkt.is_position())

    def test_is_position_false_neither(self):
        mock_sentence = MagicMock()
        mock_sentence.__contains__ = lambda self, key: False
        pkt = DataPacket("test", mock_sentence)
        self.assertFalse(pkt.is_position())


class TestDataPacketIsHeading(unittest.TestCase):
    """Tests for DataPacket.is_heading using mock sentences."""

    def test_is_heading_true(self):
        mock_sentence = MagicMock()
        mock_sentence.heading = 274.07
        pkt = DataPacket("test", mock_sentence)
        self.assertTrue(pkt.is_heading())

    def test_is_heading_false_none(self):
        mock_sentence = MagicMock()
        mock_sentence.heading = None
        pkt = DataPacket("test", mock_sentence)
        self.assertFalse(pkt.is_heading())

    def test_is_heading_false_no_attribute(self):
        mock_sentence = MagicMock(spec=[])
        pkt = DataPacket("test", mock_sentence)
        self.assertFalse(pkt.is_heading())


class TestNMEADataPacketParse(unittest.TestCase):
    """Tests for NMEADataPacket.parse with different NMEA sentence types."""

    def test_parse_gga(self):
        sentence = (
            "$GPGGA,184353.07,1929.045,S,02410.506,E,1,04,2.6,100.00,M,-33.9,M,,0000*6D"
        )
        pkt = NMEADataPacket.parse(sentence)
        self.assertEqual(pkt.data.sentence_type, "GGA")
        self.assertTrue(pkt.is_position())

    def test_parse_dbt(self):
        sentence = "$SDDBT,12.3,f,3.7,M,2.0,F*30"
        pkt = NMEADataPacket.parse(sentence)
        self.assertEqual(pkt.data.sentence_type, "DBT")
        self.assertFalse(pkt.is_position())

    def test_parse_gga_has_latitude_longitude(self):
        sentence = (
            "$GPGGA,184353.07,1929.045,S,02410.506,E,1,04,2.6,100.00,M,-33.9,M,,0000*6D"
        )
        pkt = NMEADataPacket.parse(sentence)
        self.assertNotEqual(pkt.data.latitude, 0.0)
        self.assertNotEqual(pkt.data.longitude, 0.0)

    def test_parse_rmc_is_position(self):
        sentence = "$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68"
        pkt = NMEADataPacket.parse(sentence)
        self.assertTrue(pkt.is_position())


class TestAISDataPacketBehavior(unittest.TestCase):
    """Tests for AISDataPacket.is_heading and is_position always returning False."""

    def test_is_heading_always_false(self):
        pkt = AISDataPacket("!AIVDM,1,1,,B,13u@Dt002s000000000000000000,0*59")
        self.assertFalse(pkt.is_heading())

    def test_is_position_always_false(self):
        pkt = AISDataPacket("!AIVDM,1,1,,B,13u@Dt002s000000000000000000,0*59")
        self.assertFalse(pkt.is_position())

    def test_is_heading_false_regardless_of_content(self):
        # Even with different raw content, should always be False
        pkt = AISDataPacket("!AIVDM,2,1,3,B,55?MbV02,0*25")
        self.assertFalse(pkt.is_heading())

    def test_is_position_false_regardless_of_content(self):
        pkt = AISDataPacket("!AIVDM,2,1,3,B,55?MbV02,0*25")
        self.assertFalse(pkt.is_position())


class TestDataSourceBase(unittest.TestCase):
    """Tests for DataSource base class behavior."""

    def test_init_nmea0183_protocol(self):
        ds = DataSource("nmea0183", "in")
        self.assertEqual(ds.protocol, "nmea0183")
        self.assertEqual(ds.direction, "in")
        self.assertFalse(ds.connected)
        self.assertEqual(ds.parser, NMEADataPacket)

    def test_init_unsupported_protocol_raises(self):
        with self.assertRaises(NotImplementedError):
            DataSource("unsupported", "in")

    def test_connect_returns_false(self):
        ds = DataSource("nmea0183", "in")
        result = ds.connect()
        self.assertFalse(result)

    def test_close_sets_connected_false(self):
        ds = DataSource("nmea0183", "in")
        ds.connected = True
        ds.close()
        self.assertFalse(ds.connected)

    def test_write_when_not_connected(self):
        ds = DataSource("nmea0183", "out")
        mock_packet = MagicMock()
        result = ds.write(mock_packet)
        self.assertFalse(result)

    def test_read_when_not_connected(self):
        ds = DataSource("nmea0183", "in")
        result = ds.read()
        self.assertEqual(result, [])

    def test_write_when_direction_is_in(self):
        ds = DataSource("nmea0183", "in")
        ds.connected = True
        mock_packet = MagicMock()
        result = ds.write(mock_packet)
        self.assertFalse(result)

    def test_read_when_direction_is_out(self):
        ds = DataSource("nmea0183", "out")
        ds.connected = True
        # _read is not implemented, but direction check returns [] before calling it
        result = ds.read()
        self.assertEqual(result, [])
