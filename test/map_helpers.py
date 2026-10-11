"""Windowless map canvas shared by map interaction and overlay tests."""

from unittest.mock import Mock

from gweatherrouting.gtk.widgets.mapwidget import MapViewport


class MapCanvas(MapViewport):
    __test__ = False

    def __init__(self):
        self._center_lat = 47.6
        self._center_lon = -122.4
        self._zoom = 12
        self.width = 400
        self.height = 300
        self.queue_draw = Mock()
        self.add_tick_callback = Mock(return_value=1)
        self.remove_tick_callback = Mock()
        self.factor = 1

    def get_scale_factor(self):
        return self.factor
