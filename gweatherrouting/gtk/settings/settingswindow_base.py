# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
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
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from gweatherrouting.core import Core

from .settingsmanager import SettingsManager


class SettingsWindowBase:
    builder: Gtk.Builder
    core: Core
    window: Gtk.Window
    parent: Gtk.Window
    settings_manager: SettingsManager
