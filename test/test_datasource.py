# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
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

from gweatherrouting.core.datasource import AISDataPacket, NMEADataPacket


class TestNMEADataPacket(unittest.TestCase):
    def test_parse_rmc(self):
        sentence = (
            "$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68"
        )
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
