import logging
import os
from threading import Thread

import gi
import requests

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

logger = logging.getLogger("gweatherrouting")

PolFileFilter = Gtk.FileFilter()
PolFileFilter.set_name("Polar file")
PolFileFilter.add_pattern("*.pol")


class PolarManagerWindow:
    def __init__(self, polar_manager, parent=None):
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
        if parent:
            self.window.set_transient_for(parent)
            self.window.set_modal(True)

        self.orc_ListStore = self.builder.get_object("orc-list-store")
        self.orc_filter = Gtk.TreeModelFilter(child_model=self.orc_ListStore)
        self.orc_filter.set_visible_func(self._orc_filter_func)
        self.builder.get_object("orc-treeview").set_model(self.orc_filter)
        self.orc_search_text = ""

        self.polar_managerStore = self.builder.get_object("polar-manager-store")
        self.refresh_polars_tab()
        self.polar_manager.connect("polars-list-updated", self.refresh_polars_tab)
        Thread(target=self.download_orc_list, args=()).start()

    def show(self):
        self.window.show_all()

    def close(self):
        self.window.hide()

    # ORC data management

    def on_orc_search_changed(self, widget):
        self.orc_search_text = widget.get_text().lower()
        self.orc_filter.refilter()

    def _orc_filter_func(self, model, tree_iter, data=None):
        if not self.orc_search_text:
            return True
        for col in range(3):
            val = model.get_value(tree_iter, col)
            if val and self.orc_search_text in val.lower():
                return True
        return False

    def on_orc_select(self, selection):
        store, pathlist = selection.get_selected_rows()
        if not pathlist:
            return
        tree_iter = store.get_iter(pathlist[0])
        if not store.get_value(tree_iter, 3):
            selection.unselect_iter(tree_iter)
            self.selected_orc_polar = None
            return
        self.selected_orc_polar = store.get_value(tree_iter, 0)

    def on_orc_click(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("orc-list-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def on_orc_download(self, widget):
        Thread(target=self.download_orc, args=()).start()

    # Local polar management

    def on_local_polar_click(self, widget, event):
        if event.button == 3:
            menu = self.builder.get_object("polar-manager-menu")
            menu.popup(None, None, None, None, event.button, event.time)

    def on_local_polar_select(self, selection):
        store, pathlist = selection.get_selected_rows()
        if not pathlist:
            self.selected_local_polar = None
            return
        tree_iter = store.get_iter(pathlist[0])
        self.selected_local_polar = store.get_value(tree_iter, 0)

    def on_polar_toggle(self, widget, i):
        n = self.polar_manager.polars_files[int(i)]
        if self.polar_manager.is_enabled(n):
            self.polar_manager.disable(n)
        else:
            self.polar_manager.enable(n)

    def on_local_polar_remove(self, widget):
        self.polar_manager.delete_polar(self.selected_local_polar)

    def download_orc_list(self):
        GLib.idle_add(lambda: self.builder.get_object("download-progress").show())
        orc_url = "https://raw.githubusercontent.com/jieter/orc-data/refs/heads/master/site/index.json"  # noqa: E501
        try:
            r = requests.get(orc_url)
            orc_data = r.json()
            GLib.idle_add(self._populate_orc_list, orc_data)
        except Exception:
            logger.error(f"Failed to download orc data file list from {orc_url}")
            GLib.idle_add(
                lambda: self.builder.get_object("download-progress").set_text(
                    "Failed to download orc data list"
                )
            )

    def _is_orc_downloaded(self, orc_entry):
        file_name = orc_entry[0].replace("/", "_") + ".pol"
        return file_name in self.polar_manager.polars_files

    def _populate_orc_list(self, orc_data):
        for d in orc_data:
            selectable = not self._is_orc_downloaded(d)
            self.orc_ListStore.append([*d, selectable])
        self.builder.get_object("download-progress").hide()

    def download_orc(self):
        polar_name = self.selected_orc_polar
        GLib.idle_add(
            lambda: self.builder.get_object("download-progress").set_text(
                f"Downloading {polar_name}..."
            )
        )
        GLib.idle_add(lambda: self.builder.get_object("download-progress").show())
        try:
            self.polar_manager.download_orc_polar(polar_name, dispatch=False)
            GLib.idle_add(self._on_orc_download_done, polar_name)
        except Exception:
            logger.error(f"Failed to download orc data file {polar_name}")
            GLib.idle_add(
                lambda: self.builder.get_object("download-progress").set_text(
                    f"Failed to download {polar_name}"
                )
            )

    def _on_orc_download_done(self, polar_name):
        self.builder.get_object("download-progress").set_text(
            f"Downloaded {polar_name}"
        )
        # Mark the row as no longer selectable
        for row in self.orc_ListStore:
            if row[0] == polar_name:
                row[3] = False
                break
        self.selected_orc_polar = None
        self.polar_manager.dispatch("polars-list-updated", self.polar_manager.polars)

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
            meta = self.polar_manager.get_metadata(polar)
            self.polar_managerStore.append(
                [
                    polar,
                    meta.get("sail", ""),
                    meta.get("name", ""),
                    meta.get("type", ""),
                    enabled,
                ]
            )
