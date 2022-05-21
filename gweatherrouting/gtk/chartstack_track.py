# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

import gi

gi.require_version('Gtk', '3.0')
try:
	gi.require_version('OsmGpsMap', '1.2')
except:
	gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk
from .maplayers import TrackMapLayer

from ..core import utils

class ChartStackTrack:
	selectedTrackItem = None

	def __init__(self):
		self.trackMapLayer = TrackMapLayer(self.core.trackManager, self.timeControl)
		self.map.layer_add (self.trackMapLayer)

		self.trackStore = self.builder.get_object("track-store")
		self.trackListStore = self.builder.get_object("track-list-store")
		self.updateTrack()


	def updateTrack (self, onlyActive = False):
		if not onlyActive:
			self.trackListStore.clear()
			for x in self.core.trackManager.tracks:
				self.trackListStore.append([x.name, x.size(), x.length(), x.visible])

		self.trackStore.clear ()

		if self.core.trackManager.activeTrack:
			i = 0
			for wp in self.core.trackManager.activeTrack:
				i += 1
				self.trackStore.append([i, wp[0], wp[1]])

		self.map.queue_draw()

	def onTrackExport(self, widget):
		dialog = Gtk.FileChooserDialog ("Please select a destination", self.parent,
					Gtk.FileChooserAction.SAVE,
					(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

		filter_gpx = Gtk.FileFilter()
		filter_gpx.set_name("GPX track")
		filter_gpx.add_mime_type("application/gpx+xml")
		filter_gpx.add_pattern ('*.gpx')
		dialog.add_filter(filter_gpx)

		response = dialog.run ()

		if response == Gtk.ResponseType.OK:
			filepath = dialog.get_filename ()
			
			if not filepath.endswith('.gpx'):
				filepath += '.gpx'

			if self.core.trackManager.activeTrack.export (filepath):
				# self.builder.get_object('header-bar').set_subtitle (filepath)
				self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Saved %d waypoints' % (len (self.core.trackManager.activeTrack)))
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Saved")
				edialog.format_secondary_text ('Saved %d waypoints' % (len (self.core.trackManager.activeTrack)))
				edialog.run ()
				edialog.destroy ()
			else:
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
				edialog.format_secondary_text ("Cannot save file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
			
		dialog.destroy ()


	def onTrackNameEdit(self, widget, i, name):
		self.core.trackManager.tracks[int(i)].name = utils.uniqueName(name, self.core.trackManager.tracks)
		self.updateTrack()
		
	def onTrackToggle(self, widget, i):
		self.core.trackManager.tracks[int(i)].visible = not self.core.trackManager.tracks[int(i)].visible
		self.updateTrack()

	def onTrackRemove(self, widget):
		self.core.trackManager.remove(self.core.trackManager.activeTrack)
		self.updateTrack()
		self.map.queue_draw()

	def onTrackClick(self, item, event):
		if event.button == 3 and len(self.core.trackManager.tracks) > 0:
			menu = self.builder.get_object("track-list-item-menu")
			menu.popup (None, None, None, None, event.button, event.time)

	def onTrackItemClick(self, item, event):
		if event.button == 3 and self.core.trackManager.activeTrack.size() > 0:
			menu = self.builder.get_object("track-item-menu")
			menu.popup (None, None, None, None, event.button, event.time)

	def onSelectTrack(self, selection):
		store, pathlist = selection.get_selected_rows()
		for path in pathlist:
			tree_iter = store.get_iter(path)
			name = store.get_value(tree_iter, 0)
			self.core.trackManager.activate(name)
			self.updateTrack(onlyActive=True)
			self.map.queue_draw()


	def onSelectTrackItem (self, selection):
		store, pathlist = selection.get_selected_rows()
		for path in pathlist:
			tree_iter = store.get_iter(path)
			value = store.get_value(tree_iter, 0)
			self.selectedTrackItem = int(value) - 1


	def onTrackItemMove(self, widget):
		if self.selectedTrackItem != None:
			self.toolsMapLayer.enablePOIMoving(
				lambda x,y: self.core.trackManager.activeTrack.move(self.selectedTrackItem, x, y))


	def onTrackItemMoveUp(self, widget):
		if self.selectedTrackItem != None:
			self.core.trackManager.activeTrack.moveUp(self.selectedTrackItem)
			self.updateTrack()
			self.map.queue_draw ()

	def onTrackItemMoveDown(self, widget):
		if self.selectedTrackItem != None:
			self.core.trackManager.activeTrack.moveDown(self.selectedTrackItem)
			self.updateTrack()
			self.map.queue_draw ()

	def onTrackItemRemove(self, widget):
		if self.selectedTrackItem != None:
			self.core.trackManager.activeTrack.remove(self.selectedTrackItem)
			self.updateTrack()
			self.map.queue_draw ()

	def onTrackItemDuplicate(self, widget):
		if self.selectedTrackItem != None:
			self.core.trackManager.activeTrack.duplicate(self.selectedTrackItem)
			self.updateTrack()
			self.map.queue_draw ()	

	def showTrackPointPopover(self, event):
		popover = self.builder.get_object("track-add-point-popover")
		popover.show_all()


	def addTrackPoint (self, widget):
		lat = self.builder.get_object("track-add-point-lat").get_text ()
		lon = self.builder.get_object("track-add-point-lon").get_text ()

		if len (lat) > 1 and len (lon) > 1:
			if len(self.core.trackManager.tracks) == 0:
				self.core.trackManager.create()

			self.core.trackManager.activeTrack.add (float (lat), float (lon))
			self.updateTrack ()

			self.builder.get_object("track-add-point-lat").set_text ('')
			self.builder.get_object("track-add-point-lon").set_text ('')
			self.builder.get_object("track-add-point-popover").hide()
		self.map.queue_draw ()



