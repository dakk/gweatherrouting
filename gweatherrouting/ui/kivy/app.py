from kivy_garden.mapview import MapView
# from kivy.app import App, Builder
import os
from kivymd.app import MDApp
from kivy.app import Builder

class GWeatherRoutingApp(MDApp):
    def __init__(self, core, conn):
        super(GWeatherRoutingApp, self).__init__()

    def build(self):
        return Builder.load_file(os.path.abspath(os.path.dirname(__file__)) + "/app.kv")

        mapview = MapView(zoom=11, lat=50.6394, lon=3.057)
        return mapview