import gi
from threading import Thread

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, Gdk

from .routingwizarddialog import RoutingWizardDialog
from .maplayers import IsochronesMapLayer
from ...core import RoutingTrack, utils

class MainWindowRouting:
	routingThread = None
	selectedRouting = None

	def __init__(self):
		self.routingStore = self.builder.get_object("routing-store")

		self.isochronesMapLayer = IsochronesMapLayer ()
		self.map.layer_add (self.isochronesMapLayer)

		self.updateRoutings()

	def __del__(self): 
		if self.routingThread:
			self.currentRouting.end = True

	def onRoutingCreate(self, event):
		if not self.core.gribManager.hasGrib():
			epop = self.builder.get_object('routing-nogrib-error-popover')
			epop.show_all()
			return

		if len (self.core.trackManager.activeTrack) < 2:
			epop = self.builder.get_object('routing-2points-error-popover')
			epop.show_all()
			return

		dialog = RoutingWizardDialog.create (self.core, self.window)
		response = dialog.run ()

		if response == Gtk.ResponseType.OK:
			self.currentRouting = self.core.createRouting (dialog.getSelectedAlgorithm (), dialog.getSelectedBoat (), dialog.getSelectedTrack(), dialog.getStartDateTime())
			
			self.routingThread = Thread(target=self.onRoutingStep, args=())
			self.routingThread.start()

		dialog.destroy ()
		
	def onRoutingStep (self):
		res = None 

		while not self.currentRouting.end:
			res = self.currentRouting.step ()

			Gdk.threads_enter()
			self.isochronesMapLayer.setIsochrones (res['isochrones'])
			self.timeControl.setTime(res['time'])
			# self.map.queue_draw ()
			# self.builder.get_object('time-adjustment').set_value (res['time'])
			Gdk.threads_leave()	

		tr = []
		for wp in res['path']:
			if len(wp) == 3:
				tr.append((wp[0], wp[1], str(wp[2]), 0, 0, 0, 0))
			else:
				tr.append((wp[0], wp[1], str(wp[4]), wp[5], wp[6], wp[7], wp[8]))

		self.core.trackManager.routings.append(RoutingTrack(name=utils.uniqueName('routing', self.core.trackManager.routings), waypoints=tr, trackManager=self.core.trackManager))
		self.updateRoutings()


	def updateRoutings(self):
		self.routingStore.clear()

		for r in self.core.trackManager.routings:
			riter = self.routingStore.append(None, [r.name, '', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, r.visible, False, True])

			for x in r.waypoints:
				self.routingStore.append(riter, ['', x[2], x[0], x[1], x[3], x[4], x[5], x[6], False, True, False])

		self.map.queue_draw()
		self.core.trackManager.saveTracks()

	def onRoutingToggle(self, widget, i):
		self.core.trackManager.routings[int(i)].visible = not self.core.trackManager.routings[int(i)].visible
		self.updateRoutings()
		self.updateTrack()

	def onRoutingNameEdit(self, widget, i, name):
		self.core.trackManager.routings[int(i)].name = utils.uniqueName(name, self.core.trackManager.routings)
		self.updateRoutings()
		

	def onRoutingRemove(self, widget):
		self.core.trackManager.removeRouting(self.selectedRouting)
		self.updateRoutings()
		self.map.queue_draw()

	def onRoutingExport(self, widget):
		routing = self.core.trackManager.getRouting(self.selectedRouting)

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

			if routing.export (filepath):
				self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Saved %d waypoints' % (len (routing)))
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Saved")
				edialog.format_secondary_text ('Saved %d waypoints' % (len (routing)))
				edialog.run ()
				edialog.destroy ()
			else:
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
				edialog.format_secondary_text ("Cannot save file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
			
		dialog.destroy ()

	def onSelectRouting (self, selection):
		store, pathlist = selection.get_selected_rows()
		for path in pathlist:
			tree_iter = store.get_iter(path)
			value = store.get_value(tree_iter, 0)
			if path.get_depth() == 1:
				self.selectedRouting = value
			else:
				self.selectedRouting = None

	def onRoutingClick(self, item, event):		
		if self.selectedRouting != None and event.button == 3 and len(self.core.trackManager.routings) > 0:
			menu = self.builder.get_object("routing-item-menu")
			menu.popup (None, None, None, None, event.button, event.time)