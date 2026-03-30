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

import socket
import time
import unittest
from unittest.mock import MagicMock, patch

from gweatherrouting.core.connectionmanager import ConnectionManager
from gweatherrouting.core.datasource import DataSource, NMEADataPacket
from gweatherrouting.core.networkdatasource import MAX_LINE_LENGTH, NetworkDataSource
from gweatherrouting.core.serialdatasource import SerialDataSource

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeDataSource(DataSource):
    """A DataSource subclass that returns canned data without real I/O."""

    def __init__(self, data=None, fail_on_read=False):
        super().__init__("nmea0183", "in")
        self._data = data or []
        self._fail_on_read = fail_on_read
        self.closed = False

    def connect(self):
        self.connected = True
        return True

    def close(self):
        self.closed = True
        self.connected = False

    def _read(self):
        if self._fail_on_read:
            raise OSError("fake read error")
        return self._data

    def _write(self, data):
        pass


def _make_cm():
    """Create a ConnectionManager with an empty in-memory storage."""
    cm = ConnectionManager()
    cm.storage = MagicMock()
    cm.storage.connections = []
    cm.storage.save = MagicMock()
    return cm


# ---------------------------------------------------------------------------
# ConnectionManager lifecycle tests
# ---------------------------------------------------------------------------


class TestConnectionManagerInit(unittest.TestCase):
    def test_initial_state(self):
        cm = _make_cm()
        self.assertFalse(cm.polling_active)
        self.assertEqual(cm.sources, {})
        self.assertEqual(cm.get_status(), [])
        self.assertIsNone(cm.thread)

    def test_connections_property_delegates_to_storage(self):
        cm = _make_cm()
        cm.storage.connections = [{"type": "network", "host": "h", "port": 1}]
        self.assertEqual(len(cm.connections), 1)


class TestPollingActiveProperty(unittest.TestCase):
    def test_false_before_start(self):
        cm = _make_cm()
        self.assertFalse(cm.polling_active)

    def test_true_after_start(self):
        cm = _make_cm()
        cm.start_polling()
        try:
            self.assertTrue(cm.polling_active)
        finally:
            cm.stop_polling()

    def test_false_after_stop(self):
        cm = _make_cm()
        cm.start_polling()
        cm.stop_polling()
        self.assertFalse(cm.polling_active)


# ---------------------------------------------------------------------------
# start_polling / stop_polling
# ---------------------------------------------------------------------------


class TestStartStopPolling(unittest.TestCase):
    def test_start_creates_thread(self):
        cm = _make_cm()
        cm.start_polling()
        try:
            self.assertIsNotNone(cm.thread)
            self.assertTrue(cm.thread.is_alive())
        finally:
            cm.stop_polling()

    def test_stop_joins_thread(self):
        cm = _make_cm()
        cm.start_polling()
        thread = cm.thread
        cm.stop_polling()
        self.assertFalse(thread.is_alive())
        self.assertIsNone(cm.thread)

    def test_stop_clears_sources(self):
        cm = _make_cm()
        cm.sources["key"] = FakeDataSource()
        cm.sources["key"].connect()
        cm.start_polling()
        cm.stop_polling()
        self.assertEqual(cm.sources, {})

    def test_stop_closes_sources(self):
        cm = _make_cm()
        ds = FakeDataSource()
        ds.connect()
        cm.sources["key"] = ds
        cm.start_polling()
        cm.stop_polling()
        self.assertTrue(ds.closed)

    def test_start_resets_packets(self):
        cm = _make_cm()
        cm._packets = {"old": 42}
        cm.start_polling()
        try:
            self.assertEqual(cm._packets, {})
        finally:
            cm.stop_polling()

    def test_stop_without_start_is_safe(self):
        cm = _make_cm()
        cm.stop_polling()  # should not raise


# ---------------------------------------------------------------------------
# plug_all
# ---------------------------------------------------------------------------


class TestPlugAll(unittest.TestCase):
    def test_creates_network_source(self):
        cm = _make_cm()
        cm.storage.connections = [
            {
                "type": "network",
                "protocol": "nmea0183",
                "direction": "in",
                "host": "127.0.0.1",
                "port": 10110,
                "network": "tcp",
            }
        ]
        with patch.object(NetworkDataSource, "connect", return_value=False):
            cm.plug_all()
        self.assertIn("127.0.0.1:10110", cm.sources)
        self.assertIsInstance(cm.sources["127.0.0.1:10110"], NetworkDataSource)

    def test_creates_serial_source(self):
        cm = _make_cm()
        cm.storage.connections = [
            {
                "type": "serial",
                "protocol": "nmea0183",
                "direction": "in",
                "data-port": "/dev/ttyFAKE",
                "baudrate": 9600,
            }
        ]
        with patch.object(SerialDataSource, "connect", return_value=False):
            cm.plug_all()
        self.assertIn("/dev/ttyFAKE", cm.sources)
        self.assertIsInstance(cm.sources["/dev/ttyFAKE"], SerialDataSource)

    def test_closes_old_sources_before_recreating(self):
        cm = _make_cm()
        old_ds = FakeDataSource()
        old_ds.connect()
        cm.sources["127.0.0.1:10110"] = old_ds

        cm.storage.connections = [
            {
                "type": "network",
                "protocol": "nmea0183",
                "direction": "in",
                "host": "127.0.0.1",
                "port": 10110,
                "network": "tcp",
            }
        ]
        with patch.object(NetworkDataSource, "connect", return_value=False):
            cm.plug_all()

        self.assertTrue(old_ds.closed)
        self.assertIsNot(cm.sources["127.0.0.1:10110"], old_ds)

    def test_empty_connections_clears_sources(self):
        cm = _make_cm()
        ds = FakeDataSource()
        ds.connect()
        cm.sources["key"] = ds
        cm.storage.connections = []
        cm.plug_all()
        self.assertEqual(cm.sources, {})
        self.assertTrue(ds.closed)


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus(unittest.TestCase):
    def test_empty_sources(self):
        cm = _make_cm()
        self.assertEqual(cm.get_status(), [])

    def test_single_connected_source(self):
        cm = _make_cm()
        ds = FakeDataSource()
        ds.connect()
        cm.sources["src1"] = ds
        cm._packets["src1"] = 10

        status = cm.get_status()
        self.assertEqual(len(status), 1)
        self.assertEqual(status[0]["name"], "src1")
        self.assertTrue(status[0]["connected"])
        self.assertEqual(status[0]["packets"], 10)

    def test_disconnected_source_zero_packets(self):
        cm = _make_cm()
        ds = FakeDataSource()
        cm.sources["src1"] = ds

        status = cm.get_status()
        self.assertEqual(len(status), 1)
        self.assertFalse(status[0]["connected"])
        self.assertEqual(status[0]["packets"], 0)

    def test_mixed_sources(self):
        cm = _make_cm()
        ds1 = FakeDataSource()
        ds1.connect()
        ds2 = FakeDataSource()
        cm.sources["up"] = ds1
        cm.sources["down"] = ds2
        cm._packets["up"] = 5

        status = cm.get_status()
        by_name = {s["name"]: s for s in status}
        self.assertTrue(by_name["up"]["connected"])
        self.assertFalse(by_name["down"]["connected"])


# ---------------------------------------------------------------------------
# poll
# ---------------------------------------------------------------------------


class TestPoll(unittest.TestCase):
    def test_poll_reads_connected_sources(self):
        cm = _make_cm()
        ds = FakeDataSource(
            data=["$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68"]
        )
        ds.connect()
        cm.sources["s1"] = ds

        n = cm.poll()
        self.assertEqual(n, 1)

    def test_poll_increments_packet_count(self):
        cm = _make_cm()
        ds = FakeDataSource(
            data=["$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68"]
        )
        ds.connect()
        cm.sources["s1"] = ds

        cm.poll()
        self.assertEqual(cm._packets["s1"], 1)

        cm.poll()
        self.assertEqual(cm._packets["s1"], 2)

    def test_poll_skips_disconnected_sources(self):
        cm = _make_cm()
        ds = FakeDataSource(data=["sentence"])
        # not connected
        cm.sources["s1"] = ds

        n = cm.poll()
        self.assertEqual(n, 0)

    def test_poll_dispatches_data_event(self):
        cm = _make_cm()
        ds = FakeDataSource(
            data=["$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68"]
        )
        ds.connect()
        cm.sources["s1"] = ds

        received = []
        cm.connect("data", lambda d: received.extend(d))
        cm.poll()
        self.assertEqual(len(received), 1)

    def test_poll_no_dispatch_when_no_data(self):
        cm = _make_cm()
        ds = FakeDataSource(data=[])
        ds.connect()
        cm.sources["s1"] = ds

        received = []
        cm.connect("data", lambda d: received.extend(d))
        cm.poll()
        self.assertEqual(len(received), 0)

    def test_poll_marks_source_disconnected_on_read_exception(self):
        cm = _make_cm()
        ds = FakeDataSource(fail_on_read=True)
        ds.connect()
        cm.sources["s1"] = ds

        cm.poll()
        self.assertFalse(ds.connected)

    def test_poll_triggers_reconnect_when_source_disconnected(self):
        cm = _make_cm()
        ds = FakeDataSource()
        # connected source + disconnected source
        ds_up = FakeDataSource(data=[])
        ds_up.connect()
        cm.sources["up"] = ds_up
        cm.sources["down"] = ds  # not connected

        with patch.object(cm, "plug_all") as mock_plug:
            cm.poll()
            mock_plug.assert_called_once()

    def test_poll_no_reconnect_when_all_connected(self):
        cm = _make_cm()
        ds = FakeDataSource(data=[])
        ds.connect()
        cm.sources["s1"] = ds

        with patch.object(cm, "plug_all") as mock_plug:
            cm.poll()
            mock_plug.assert_not_called()

    def test_poll_no_reconnect_when_no_sources(self):
        cm = _make_cm()
        with patch.object(cm, "plug_all") as mock_plug:
            cm.poll()
            mock_plug.assert_not_called()

    def test_poll_multiple_sources_aggregates_data(self):
        cm = _make_cm()
        ds1 = FakeDataSource(
            data=["$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68"]
        )
        ds1.connect()
        ds2 = FakeDataSource(data=["$IIMWV,045.0,R,12.5,N,A*0A"])
        ds2.connect()
        cm.sources["s1"] = ds1
        cm.sources["s2"] = ds2

        n = cm.poll()
        self.assertEqual(n, 2)
        self.assertEqual(cm._packets["s1"], 1)
        self.assertEqual(cm._packets["s2"], 1)


# ---------------------------------------------------------------------------
# add_connection / remove_connection
# ---------------------------------------------------------------------------


class TestAddRemoveConnection(unittest.TestCase):
    def test_add_network_connection(self):
        cm = _make_cm()
        conn = {
            "type": "network",
            "protocol": "nmea0183",
            "direction": "in",
            "host": "127.0.0.1",
            "port": 10110,
            "network": "tcp",
        }
        with patch.object(cm, "plug_all"):
            cm.add_connection(conn)
        self.assertIn(conn, cm.storage.connections)
        cm.storage.save.assert_called()

    def test_add_serial_connection(self):
        cm = _make_cm()
        conn = {
            "type": "serial",
            "protocol": "nmea0183",
            "direction": "in",
            "data-port": "/dev/ttyFAKE",
            "baudrate": 9600,
        }
        with patch.object(cm, "plug_all"):
            cm.add_connection(conn)
        self.assertIn(conn, cm.storage.connections)

    def test_add_duplicate_network_ignored(self):
        cm = _make_cm()
        conn = {
            "type": "network",
            "protocol": "nmea0183",
            "direction": "in",
            "host": "127.0.0.1",
            "port": 10110,
            "network": "tcp",
        }
        with patch.object(cm, "plug_all"):
            cm.add_connection(conn)
            cm.add_connection(conn)
        self.assertEqual(len(cm.storage.connections), 1)

    def test_add_duplicate_serial_ignored(self):
        cm = _make_cm()
        conn = {
            "type": "serial",
            "protocol": "nmea0183",
            "direction": "in",
            "data-port": "/dev/ttyFAKE",
            "baudrate": 9600,
        }
        with patch.object(cm, "plug_all"):
            cm.add_connection(conn)
            cm.add_connection(conn)
        self.assertEqual(len(cm.storage.connections), 1)

    def test_remove_connection(self):
        cm = _make_cm()
        conn = {
            "type": "network",
            "protocol": "nmea0183",
            "direction": "in",
            "host": "127.0.0.1",
            "port": 10110,
            "network": "tcp",
        }
        cm.storage.connections.append(conn)
        with patch.object(cm, "plug_all"):
            cm.remove_connection(conn)
        self.assertEqual(len(cm.storage.connections), 0)
        cm.storage.save.assert_called()

    def test_add_calls_plug_all(self):
        cm = _make_cm()
        conn = {
            "type": "network",
            "protocol": "nmea0183",
            "direction": "in",
            "host": "127.0.0.1",
            "port": 10110,
            "network": "tcp",
        }
        with patch.object(cm, "plug_all") as mock_plug:
            cm.add_connection(conn)
            mock_plug.assert_called_once()

    def test_remove_calls_plug_all(self):
        cm = _make_cm()
        conn = {"type": "network", "host": "h", "port": 1}
        cm.storage.connections.append(conn)
        with patch.object(cm, "plug_all") as mock_plug:
            cm.remove_connection(conn)
            mock_plug.assert_called_once()


# ---------------------------------------------------------------------------
# Full polling lifecycle (integration-ish)
# ---------------------------------------------------------------------------


class TestPollingLifecycle(unittest.TestCase):
    def test_start_poll_stop_cycle(self):
        cm = _make_cm()
        ds = FakeDataSource(data=[])
        ds.connect()
        cm.sources["s1"] = ds

        cm.start_polling()
        self.assertTrue(cm.polling_active)
        time.sleep(0.2)
        cm.stop_polling()

        self.assertFalse(cm.polling_active)
        self.assertIsNone(cm.thread)
        self.assertEqual(cm.sources, {})

    def test_rapid_start_stop(self):
        cm = _make_cm()
        for _ in range(5):
            cm.start_polling()
            cm.stop_polling()
        self.assertFalse(cm.polling_active)

    def test_stop_during_reconnect_wait(self):
        """stop_polling should unblock the 5s reconnect wait promptly."""
        cm = _make_cm()
        ds = FakeDataSource()
        # disconnected source will trigger reconnect wait
        cm.sources["s1"] = ds
        ds_up = FakeDataSource(data=[])
        ds_up.connect()
        cm.sources["s2"] = ds_up

        cm.start_polling()
        time.sleep(0.3)
        t0 = time.monotonic()
        cm.stop_polling()
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, 3.0, "stop_polling should not block for the full reconnect timeout"
        )


# ---------------------------------------------------------------------------
# NetworkDataSource
# ---------------------------------------------------------------------------


class TestNetworkDataSourceClose(unittest.TestCase):
    def test_close_sets_disconnected(self):
        with patch("socket.socket"):
            ds = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds.connected = True
            ds.close()
            self.assertFalse(ds.connected)

    def test_close_calls_socket_close(self):
        with patch("socket.socket") as MockSocket:
            mock_sock = MockSocket.return_value
            ds = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds.close()
            mock_sock.close.assert_called_once()


class TestNetworkDataSourceRead(unittest.TestCase):
    def test_read_returns_lines(self):
        with patch("socket.socket") as MockSocket:
            mock_sock = MockSocket.return_value
            mock_sock.recv.return_value = b"$GPRMC,data1\n$GPRMC,data2\n"
            ds = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds.connected = True

            lines = ds._read()
            self.assertEqual(len(lines), 2)

    def test_read_caches_partial_line(self):
        with patch("socket.socket") as MockSocket:
            mock_sock = MockSocket.return_value
            mock_sock.recv.return_value = b"$GPRMC,data1\npartial"
            ds = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds.connected = True

            lines = ds._read()
            self.assertEqual(len(lines), 1)
            self.assertEqual(ds.cached, "partial")

    def test_read_oserror_sets_disconnected(self):
        with patch("socket.socket") as MockSocket:
            mock_sock = MockSocket.return_value
            mock_sock.recv.side_effect = OSError("connection reset")
            ds = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds.connected = True

            result = ds._read()
            self.assertEqual(result, [])
            self.assertFalse(ds.connected)

    def test_read_peer_disconnect_zero_bytes(self):
        with patch("socket.socket") as MockSocket:
            mock_sock = MockSocket.return_value
            mock_sock.recv.return_value = b""
            ds = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds.connected = True

            result = ds._read()
            self.assertEqual(result, [])
            self.assertFalse(ds.connected)

    def test_read_timeout_returns_empty(self):
        with patch("socket.socket") as MockSocket:
            mock_sock = MockSocket.return_value
            mock_sock.recv.side_effect = socket.timeout("timed out")
            ds = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds.connected = True

            result = ds._read()
            self.assertEqual(result, [])
            self.assertTrue(ds.connected)

    def test_read_oversized_line_discarded(self):
        with patch("socket.socket") as MockSocket:
            mock_sock = MockSocket.return_value
            # Return a chunk larger than MAX_LINE_LENGTH with no newline
            mock_sock.recv.return_value = b"A" * (MAX_LINE_LENGTH + 1)
            ds = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds.connected = True

            result = ds._read()
            self.assertEqual(result, [])
            self.assertEqual(ds.cached, "")

    def test_cached_is_per_instance(self):
        with patch("socket.socket"):
            ds1 = NetworkDataSource("nmea0183", "in", "localhost", 10110, "tcp")
            ds2 = NetworkDataSource("nmea0183", "in", "localhost", 10111, "tcp")
            ds1.cached = "leftover"
            self.assertEqual(ds2.cached, "")


# ---------------------------------------------------------------------------
# SerialDataSource
# ---------------------------------------------------------------------------


class TestSerialDataSourceClose(unittest.TestCase):
    def test_close_sets_disconnected(self):
        ds = SerialDataSource("nmea0183", "in", "/dev/ttyFAKE", 9600)
        ds.serial_conn = MagicMock()
        ds.connected = True
        ds.close()
        self.assertFalse(ds.connected)
        self.assertIsNone(ds.serial_conn)

    def test_close_calls_serial_close(self):
        mock_serial = MagicMock()
        ds = SerialDataSource("nmea0183", "in", "/dev/ttyFAKE", 9600)
        ds.serial_conn = mock_serial
        ds.connected = True
        ds.close()
        mock_serial.close.assert_called_once()

    def test_close_when_already_closed(self):
        ds = SerialDataSource("nmea0183", "in", "/dev/ttyFAKE", 9600)
        ds.close()  # should not raise

    def test_read_serial_exception_sets_disconnected(self):
        import serial

        mock_serial = MagicMock()
        mock_serial.inWaiting.side_effect = serial.SerialException("device lost")
        ds = SerialDataSource("nmea0183", "in", "/dev/ttyFAKE", 9600)
        ds.serial_conn = mock_serial
        ds.connected = True

        result = ds._read()
        self.assertEqual(result, [])
        self.assertFalse(ds.connected)


# ---------------------------------------------------------------------------
# EventDispatcher instance isolation
# ---------------------------------------------------------------------------


class TestEventDispatcherIsolation(unittest.TestCase):
    def test_two_instances_independent_handlers(self):
        cm1 = _make_cm()
        cm2 = _make_cm()
        received1 = []
        received2 = []
        cm1.connect("data", lambda d: received1.append(d))
        cm2.connect("data", lambda d: received2.append(d))

        cm1.dispatch("data", "hello")
        self.assertEqual(received1, ["hello"])
        self.assertEqual(received2, [])


if __name__ == "__main__":
    unittest.main()
