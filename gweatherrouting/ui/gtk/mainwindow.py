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
import math
from threading import Thread

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, Gdk

from ... import config
from .aboutdialog import AboutDialog
from .routingwizarddialog import RoutingWizardDialog
from .gribselectdialog import GribSelectDialog
from .maplayers import GribMapLayer
from .maplayers import IsochronesMapLayer



class MainWindow:
	def create (core):
		return MainWindow(core)

	def __init__(self, core):
		self.play = False
		self.openedFile = None
		self.selectedTrackItem = None
		self.core = core

		self.builder = Gtk.Builder()
		self.builder.add_from_file("./gweatherrouting/ui/gtk/mainwindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object("main-window")
		self.window.connect("delete-event", Gtk.main_quit)
		self.window.show_all()

		self.window.set_default_size (800, 600)
		self.window.maximize ()

		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		self.isochronesMapLayer = IsochronesMapLayer ()
		self.map.layer_add (self.isochronesMapLayer)
		self.gribMapLayer = GribMapLayer (self.core.grib)
		self.map.layer_add (self.gribMapLayer)
		self.map.layer_add (OsmGpsMap.MapOsd (show_dpad=True, show_zoom=True, show_crosshair=False))

		self.map.gps_add(39,9,99)

		self.mapTrack = OsmGpsMap.MapTrack ()
		# This will cause segfault, maybe an osm-gps-map bug
		# self.mapTrack.set_property ("editable", True)
		self.mapTrack.set_property ("line-width", 2)
		self.mapTrack.set_property ("color", Gdk.RGBA(1.0,1.0,1.0,1.0))
		self.map.track_add (self.mapTrack)

		self.statusbar = self.builder.get_object("status-bar")
		self.trackStore = self.builder.get_object("track-list-store")



	####################################
	## Routing

	def onRoutingCreate(self, event):
		if len (self.core.getTrack ()) < 2:
			edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
			edialog.format_secondary_text ("You need at least 2 track points to create a routing path")
			edialog.run ()
			edialog.destroy ()
			return

		dialog = RoutingWizardDialog.create ()
		response = dialog.run ()

		if response == Gtk.ResponseType.OK:
			self.currentRouting = self.core.createRouting (dialog.getSelectedAlgorithm (), dialog.getSelectedBoat (), dialog.getInitialTime ())
			# self.notebook.set_current_page (1)
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

		if not self.currentRouting.isEnd ():
			GObject.timeout_add (1000, self.onRoutingStep)


	####################################
	## Track handling

	def updateTrack (self):
		self.trackStore.clear ()
		while self.mapTrack.n_points() > 0:
			self.mapTrack.remove_point(0)

		i = 0
		for wp in self.core.getTrack ():
			i += 1
			self.trackStore.append([i, wp[0], wp[1]])

			p = OsmGpsMap.MapPoint ()
			p.set_degrees (wp[0], wp[1])
			self.mapTrack.add_point (p)

	def onMapClickRelease(self, map, event):
		return 

		self.trackStore.clear ()

		i = 0
		while i < self.mapTrack.n_points():
			p = self.mapTrack.get_point(i)
			d = p.get_degrees()
			self.trackStore.append([d.lat, d.lon])
			i += 1


	def onTrackItemClick(self, item, event):
		if event.button == 3 and self.core.getTrack().size() > 0:
			menu = self.builder.get_object("track-item-menu")
			menu.popup (None, None, None, None, event.button, event.time)

	def onSelectTrackItem (self, selection):
		store, pathlist = selection.get_selected_rows()
		for path in pathlist:
			tree_iter = store.get_iter(path)
			value = store.get_value(tree_iter, 0)
			self.selectedTrackItem = int(value) - 1
			print ('Selected: ', self.selectedTrackItem)

	def onTrackItemMoveUp(self, widget):
		if self.selectedTrackItem != None:
			self.core.getTrack().moveUp(self.selectedTrackItem)
			self.updateTrack()

	def onTrackItemMoveDown(self, widget):
		if self.selectedTrackItem != None:
			self.core.getTrack().moveDown(self.selectedTrackItem)
			self.updateTrack()

	def onTrackItemRemove(self, widget):
		if self.selectedTrackItem != None:
			self.core.getTrack().remove(self.selectedTrackItem)
			self.updateTrack()

	def onTrackItemDuplicate(self, widget):
		if self.selectedTrackItem != None:
			self.core.getTrack().duplicate(self.selectedTrackItem)
			self.updateTrack()


	def onMapClick(self, map, event):
		lat, lon = map.get_event_location (event).get_degrees ()
		self.builder.get_object("track-add-point-lat").set_text (str (lat))
		self.builder.get_object("track-add-point-lon").set_text (str (lon))
		self.statusbar.push(self.statusbar.get_context_id ('Info'), "Clicked on " + str(lat) + " " + str(lon))
		
		if event.button == 3:
			menu = self.builder.get_object("map-context-menu")
			menu.popup (None, None, None, None, event.button, event.time)


	def showTrackPointPopover(self, event):
		popover = self.builder.get_object("track-add-point-popover")
		popover.show_all()


	def addTrackPoint (self, widget):
		lat = self.builder.get_object("track-add-point-lat").get_text ()
		lon = self.builder.get_object("track-add-point-lon").get_text ()

		if len (lat) > 1 and len (lon) > 1:
			self.core.getTrack ().add (float (lat), float (lon))
			self.updateTrack ()

			self.builder.get_object("track-add-point-lat").set_text ('')
			self.builder.get_object("track-add-point-lon").set_text ('')
			self.builder.get_object("track-add-point-popover").hide()



	####################################
	## File handling

	def onNew (self, widget):
		self.openedFile = None
		self.core.getTrack ().clear ()
		self.updateTrack ()
		self.builder.get_object('header-bar').set_subtitle ('unsaved')

	def onSave (self, widget):
		if self.openedFile == None:
			return self.onSaveAs (widget)

		if self.core.save (self.openedFile):
			self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Saved %d waypoints to %s' % (len (self.core.getTrack ()), self.openedFile))					
		else:
			edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
			edialog.format_secondary_text ("Cannot save file: %s" % self.openedFile)
			edialog.run ()
			edialog.destroy ()


	def onSaveAs (self, widget):
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

			if self.core.save (filepath):
				self.openedFile = filepath
				self.builder.get_object('header-bar').set_subtitle (filepath)
				self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Saved %d waypoints to %s' % (len (self.core.getTrack ()), self.openedFile))
			else:
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
				edialog.format_secondary_text ("Cannot save file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
			
		dialog.destroy ()


	def onOpen (self, widget):
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

			if self.core.load (filepath):
				self.builder.get_object('header-bar').set_subtitle (filepath)
				self.openedFile = filepath
				self.updateTrack ()
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done")
				edialog.format_secondary_text ("File opened, loaded %d waypoints" % len (self.core.getTrack ()))
				edialog.run ()
				edialog.destroy ()	
				self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Loaded %s with %d waypoints' % (filepath, len (self.core.getTrack ())))					
				
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
		dialog = AboutDialog (self.window)
		response = dialog.run ()
		dialog.destroy ()


	# Grib
	def onGribOpen(self, widget):
		pass

	def onGribDownloadPercentage (self, percentage):
		self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Downloading grib: %d%% completed' % percentage)

	def onGribDownloadCompleted (self, status):
		if status:
			edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done")
			edialog.format_secondary_text ("Grib downloaded successfully")
			edialog.run ()
			edialog.destroy ()	
		else:
			edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
			edialog.format_secondary_text ("Error during grib download")
			edialog.run ()
			edialog.destroy ()	


	def onGribSelect (self, widget):
		dialog = GribSelectDialog (self.window)
		response = dialog.run()

		if response == Gtk.ResponseType.OK:
			selectedGrib = dialog.get_selected_grib ()
			t = Thread(target=self.core.grib.download, args=(selectedGrib, self.onGribDownloadPercentage, self.onGribDownloadCompleted,))
			t.start ()
		elif response == Gtk.ResponseType.CANCEL:
			pass

		dialog.destroy()