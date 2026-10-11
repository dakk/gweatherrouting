"""Live display and map interaction preferences."""

from .settingswindow_base import SettingsWindowBase


class SettingsWindowDisplay(SettingsWindowBase):
    def __init__(self):
        self._loading_display = True
        self.builder.get_object("smooth-zoom").set_active(
            self.settings_manager["smoothZoom"]
        )
        self.builder.get_object("pan-inertia").set_active(
            self.settings_manager["panInertia"]
        )
        self._loading_display = False

    def on_smooth_zoom_changed(self, widget, parameter):
        if not getattr(self, "_loading_display", True):
            self.settings_manager.smoothZoom = widget.get_active()

    def on_pan_inertia_changed(self, widget, parameter):
        if not getattr(self, "_loading_display", True):
            self.settings_manager.panInertia = widget.get_active()
