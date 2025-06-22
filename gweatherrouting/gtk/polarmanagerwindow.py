import logging
import os
from threading import Thread

import gi
import requests
import shutil
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GObject, Gtk
from gweatherrouting.core.storage import POLAR_DIR, Storage
from gweatherrouting.common import resource_path
from gweatherrouting.core.polarmanager import PolarManager
 
logger = logging.getLogger("gweatherrouting")

PolFileFilter = Gtk.FileFilter()
PolFileFilter.set_name("Polar file")
PolFileFilter.add_pattern("*.pol")

class PolarManagerWindow:
    def __init__(self,  polar_manager):
        self.polar_manager = polar_manager
        self.selected_orc_polar = None
        self.selectedLocal_polar = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/polarmanagerwindow.glade"
        )
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("polar-manager-window")
        self.window.set_default_size(550, 300)

        self.orc_ListStore = self.builder.get_object("orc-list-store")
        self.polar_managerStore = self.builder.get_object("polar-manager-store")
        self.refresh_polars_tab()
        self.polar_manager.connect("polars-list-updated", self.refresh_polars_tab)
        Thread(target=self.download_orc_list, args=()).start()

    def show(self):
        self.window.show_all()

    def close(self):
        self.window.hide()

    def on_remove_local_polar(self, widget):
        pass

    def on_orc_polar_select(self, selection):
        store, pathlist = selection.get_selected_rows()
        tree_iter = store.get_iter(pathlist[0])
        self.selected_orc_polar = store.get_value(tree_iter, 0)

    def on_polar_click(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("orc-list-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def on_local_polar_select(self, selection):
        pass

    def on_polar_toggle(self, widget, i):
        n = self.polar_manager.polars_files[int(i)]
        if self.polar_manager.is_enabled(n):
            self.polar_manager.disable(n)
        else:
            self.polar_manager.enable(n)

    def on_local_polar_click(self, widget, event):
        pass

    def on_orc_download(self, widget):
        Thread(target=self.download_orc, args=()).start()
     
    def download_orc_list(self):
        Gdk.threads_enter()
        self.builder.get_object("download-progress").show()
        Gdk.threads_leave()
        orc_url = (
            "https://raw.githubusercontent.com/jieter/orc-data/refs/heads/master/site/index.json"
        )
        Gdk.threads_enter()
        try:
            r = requests.get(orc_url)
            orc_data = r.json()
            for d in orc_data:
                self.orc_ListStore.append(d)
        except:
            logger.error(f"Failed to download orc data file list from {orc_url}")
            self.builder.get_object("download-progress").set_text(
                "Failed to download orc data list"
            )

            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Download failed",
            )
            dialog.format_secondary_text("Failed to download orc data list")
            dialog.run()
            dialog.destroy()

        Gdk.threads_leave()

    def download_orc(self):
        Gdk.threads_enter()
        try:
            self.polar_manager.download_orc_polar(self.selected_orc_polar)
        except:
            logger.error(f"Failed to download orc data file {self.selected_orc_polar}")
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Download failed",
           )
            dialog.format_secondary_text(f"Failed to download {self.selected_orc_polar} polar file")
            dialog.run()
            dialog.destroy()  
        Gdk.threads_leave()
    
    def on_open(self, widget):
        parent_window = self.window
        dialog = Gtk.FileChooserDialog(
            "Please choose a file",
            parent_window,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        dialog.add_filter(PolFileFilter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            self.polar_manager.add_polar_file(filepath)
            dialog.destroy()
    
    def refresh_polars_tab(self, widget=None):
        self.polar_managerStore.clear()
        for polar in self.polar_manager.polars_files:
            enabled = self.polar_manager.is_enabled(polar)
            self.polar_managerStore.append([polar, '-', '-', enabled])
        