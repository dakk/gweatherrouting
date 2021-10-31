from kivy_garden.mapview import MapView
from kivy.app import App

class GWeatherRoutingApp(App):
    def __init__(self, core, conn):
        super(GWeatherRoutingApp, self).__init__()

    def build(self):
        mapview = MapView(zoom=11, lat=50.6394, lon=3.057)
        return mapview