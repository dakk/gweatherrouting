import gi
import math
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from .. import config
from .mapwidget import MapWidget

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='FileOpen' />
      <menuitem action='FileSave' />
      <separator />
      <menuitem action='FileQuit' />
    </menu>
  </menubar>
</ui>
"""


class MainWindow(Gtk.Window):
    def __init__(self, core):
        Gtk.Window.__init__(self, title="Regatta Simulator")
        self.core = core
        self.set_default_size(800, 600)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Menu
        self._menubar = self.createMenuBar ()
        box.pack_start (self._menubar, False, False, 0)

        ## Center
        boxcenter = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start (boxcenter, True, True, 0)

        # Map area
        self._mapwidget = MapWidget ()
        boxcenter.pack_start (self._mapwidget, True, True, 0)

        # Status bar
        self._statusbar = Gtk.Statusbar ()
        self._statusbar.push (self._statusbar.get_context_id ('Info'), 'Regatta Simulator started.')
        box.pack_start (self._statusbar, False, False, 0)

        self.add (box)
        self.show_all ()


    def createMenuBar (self):
        # Create the menu
        action_group = Gtk.ActionGroup ("actions")

        action_filemenu = Gtk.Action ("FileMenu", "File", None, None)
        action_group.add_action(action_filemenu)

        act = Gtk.Action ("FileOpen", None, None, Gtk.STOCK_OPEN)
        act.connect ("activate", self.onQuit)
        action_group.add_action (act)
        
        act = Gtk.Action ("FileSave", None, None, Gtk.STOCK_SAVE)
        act.connect ("activate", self.onQuit)
        action_group.add_action (act)

        act = Gtk.Action ("FileQuit", None, None, Gtk.STOCK_QUIT)
        act.connect ("activate", self.onQuit)
        action_group.add_action (act)

        uimanager = Gtk.UIManager ()
        uimanager.add_ui_from_string (UI_INFO)
        accelgroup = uimanager.get_accel_group ()
        self.add_accel_group (accelgroup)

        uimanager.insert_action_group (action_group)
        return uimanager.get_widget ("/MenuBar")
        

    def onQuit (self, widget):
        Gtk.main_quit ()

