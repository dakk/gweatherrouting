import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .. import config

class MainWindow (Gtk.Window):
    def __init__ (self, core):
        super ().__init__ ()
        self.core = core
        self.set_title ('Regatta Simulator')
    