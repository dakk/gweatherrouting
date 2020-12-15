# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
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

import time
import gi
import gc
import copy
import math
from threading import Thread

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, Gdk

from ... import log, session
from .routingwizarddialog import RoutingWizardDialog
from .settingswindow import SettingsWindow
from .projectpropertieswindow import ProjectPropertiesWindow
from .gribmanagerwindow import GribManagerWindow
from .maplayers import GribMapLayer, IsochronesMapLayer, TrackMapLayer



class MainWindow:
	def create (core):
		return MainWindow(core)

	def __init__(self, core):
		self.play = False
		self.selectedTrackItem = None
		self.core = core

		self.builder = Gtk.Builder()
		self.builder.add_from_file("./gweatherrouting/ui/gtk/mainwindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object("main-window")
		self.window.connect("delete-event", Gtk.main_quit)
		self.window.set_default_size (1024, 600)
		self.window.show_all()
		# self.window.maximize ()

		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		self.isochronesMapLayer = IsochronesMapLayer ()
		self.map.layer_add (self.isochronesMapLayer)
		self.gribMapLayer = GribMapLayer (self.core.gribManager)
		self.map.layer_add (self.gribMapLayer)
		self.trackMapLayer = TrackMapLayer(self.core.trackManager)
		self.map.layer_add (self.trackMapLayer)
		self.map.layer_add (OsmGpsMap.MapOsd (show_dpad=True, show_zoom=True, show_crosshair=False))

		# self.map.gps_add(39,9,99)

		self.statusbar = self.builder.get_object("status-bar")
		self.trackStore = self.builder.get_object("track-store")
		self.trackListStore = self.builder.get_object("track-list-store")

		self.updateTrack()

	####################################
	## Routing

	def onRoutingCreate(self, event):
		if not self.core.gribManager.hasGrib():
			epop = self.builder.get_object('routing-nogrib-error-popover')
			epop.show_all()
			return

		if len (self.core.trackManager.activeTrack) < 2:
			epop = self.builder.get_object('routing-2points-error-popover')
			epop.show_all()
			return

		dialog = RoutingWizardDialog.create (self.core)
		response = dialog.run ()

		if response == Gtk.ResponseType.OK:
			self.currentRouting = self.core.createRouting (dialog.getSelectedAlgorithm (), dialog.getSelectedBoat (), dialog.getInitialTime (), dialog.getSelectedTrack())
			GObject.timeout_add (10, self.onRoutingStep)

		dialog.destroy ()
		
	def onRoutingStep (self):
		res = self.currentRouting.step ()
		self.isochronesMapLayer.setIsochrones (res['isochrones'])
		self.gribMapLayer.time = res['time']
		self.map.queue_draw ()
		self.builder.get_object('time-adjustment').set_value (res['time'])

		track = OsmGpsMap.MapTrack ()
		track.set_property ("line-width", 5)
		for wp in res['path']:
			p = OsmGpsMap.MapPoint ()
			p.set_degrees (wp[0], wp[1])
			track.add_point (p)
		
		self.map.track_add (track)		

		if not self.currentRouting.end:
			GObject.timeout_add (1000, self.onRoutingStep)


	####################################
	## Track handling

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

	def onTrackExport(self, widget):
		dialog = Gtk.FileChooserDialog ("Please select a destination", self.window,
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
			else:
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
				edialog.format_secondary_text ("Cannot save file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
			
		dialog.destroy ()
		
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


	def onMapClick(self, map, event):
		lat, lon = map.get_event_location (event).get_degrees ()
		self.builder.get_object("track-add-point-lat").set_text (str (lat))
		self.builder.get_object("track-add-point-lon").set_text (str (lon))
		self.statusbar.push(self.statusbar.get_context_id ('Info'), "Clicked on " + str(lat) + " " + str(lon))
		
		if event.button == 3:
			menu = self.builder.get_object("map-context-menu")
			menu.popup (None, None, None, None, event.button, event.time)
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



	####################################
	## File handling

	def onNew (self, widget):
		self.core.trackManager.create()
		self.updateTrack ()
		self.map.queue_draw ()
		# self.builder.get_object('header-bar').set_subtitle ('unsaved')



	def onImport (self, widget):
		dialog = Gtk.FileChooserDialog ("Please choose a file", self.window,
					Gtk.FileChooserAction.OPEN,
					(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
			
		filter_gpx = Gtk.FileFilter ()
		filter_gpx.set_name ("GPX track")
		filter_gpx.add_mime_type ("application/gpx+xml")
		filter_gpx.add_pattern ('*.gpx')
		dialog.add_filter (filter_gpx)

		response = dialog.run()
		
		if response == Gtk.ResponseType.OK:
			filepath = dialog.get_filename ()
			dialog.destroy ()

			if self.core.trackManager.importTrack (filepath):
				# self.builder.get_object('header-bar').set_subtitle (filepath)
				self.updateTrack ()
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done")
				edialog.format_secondary_text ("File opened, loaded %d waypoints" % len (self.core.trackManager.activeTrack))
				edialog.run ()
				edialog.destroy ()	
				self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Loaded %s with %d waypoints' % (filepath, len (self.core.trackManager.activeTrack)))					
				
			else:
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
				edialog.format_secondary_text ("Cannot open file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
		else:
			dialog.destroy()



	####################################
	## Time controls

	def onPlayClick(self, event):
		self.play = True
		GObject.timeout_add (10, self.onPlayStep)

	def onPlayStep(self):
		self.onFowardClick(None)
		if self.play:
			GObject.timeout_add (1000, self.onPlayStep)

	def onStopClick(self, event):
		self.play = False

	def onFowardClick(self, event):
		self.gribMapLayer.time += 1
		self.map.queue_draw ()
		self.updateTimeSlider()

	def onBackwardClick(self, event):
		if self.gribMapLayer.time > 0:
			self.gribMapLayer.time -= 1
			self.map.queue_draw ()
			self.updateTimeSlider()

	def updateTimeSlider(self):
		self.builder.get_object('time-adjustment').set_value(int(self.gribMapLayer.time))

	def onTimeSlide (self, widget):
		self.gribMapLayer.time = int (self.builder.get_object('time-adjustment').get_value())
		self.map.queue_draw ()


	####################################
	# Misc
	def onAbout(self, item):
		dialog = self.builder.get_object('about-dialog')
		response = dialog.run ()
		dialog.hide ()

	def onSettings(self, event):
		w = SettingsWindow.create ()
		w.show ()

	def onProjectProperties(self, event):
		w = ProjectPropertiesWindow.create ()
		w.show ()

	def onGribManager(self, event):
		w = GribManagerWindow.create (self.core.gribManager)
		w.show ()
