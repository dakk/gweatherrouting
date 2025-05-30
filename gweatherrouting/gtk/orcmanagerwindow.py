import logging
import os
from threading import Thread

import gi
import requests

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk

logger = logging.getLogger("gweatherrouting")


class OrcManagerWindow:
    def __init__(self):
        self.selected_ORCboat = None
        self.selectedLocal_ORCboat = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/orcmanagerwindow.glade"
        )
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("orc-manager-window")
        self.window.set_default_size(550, 300)

        self.orcFilesStore = self.builder.get_object("orc-files-store")
        self.orc_managerStore = self.builder.get_object("orc-manager-store")

        # self.update_local_orcboats()

        Thread(target=self.download_list, args=()).start()

    def show(self):
        self.window.show_all()

    def close(self):
        self.window.hide()

    def on_remove_local_orc(self, widget):
        pass

    def on_orc_select(self, selection):
        pass

    def on_orc_click(self, widget, event):
        pass

    def on_local_orc_select(self, selection):
        pass

    def on_orc_toggle(self, widget, i):
        pass

    def on_local_orc_click(self, widget, event):
        pass

    def on_orc_download(self, widget):
        pass

    def download_list(self):
        Gdk.threads_enter()
        self.builder.get_object("download-progress").show()
        Gdk.threads_leave()
        orc_url = (
            "https://raw.githubusercontent.com/jieter/orc-data"
            "/refs/heads/master/site/index.json"
        )
        Gdk.threads_enter()
        try:
            r = requests.get(orc_url)
            orc_data = r.json()
            for d in orc_data:
                self.orcFilesStore.append(d)
            Gdk.threads_leave()
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
