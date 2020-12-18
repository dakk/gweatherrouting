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
			self.currentRouting = self.core.createRouting (dialog.getSelectedAlgorithm (), dialog.getSelectedBoat (), dialog.getInitialTime (), dialog.getSelectedTrack())
			
			self.routingThread = Thread(target=self.onRoutingStep, args=())
			self.routingThread.start()

		dialog.destroy ()
		
	def onRoutingStep (self):
		res = None 

		while not self.currentRouting.end:
			res = self.currentRouting.step ()

			Gdk.threads_enter()
			self.isochronesMapLayer.setIsochrones (res['isochrones'])
			self.gribMapLayer.time = res['time']
			self.map.queue_draw ()
			self.builder.get_object('time-adjustment').set_value (res['time'])
			Gdk.threads_leave()	

		tr = []
		for wp in res['path']:
			tr.append((wp[0], wp[1], wp[-1]))

		self.core.trackManager.routings.append(RoutingTrack(waypoints=tr, trackManager=self.core.trackManager))
		self.updateRoutings()


	def updateRoutings(self):
		self.routingStore.clear()

		for r in self.core.trackManager.routings:
			riter = self.routingStore.append(None, [r.name, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, r.visible, False, True])

			for x in r.waypoints:
				self.routingStore.append(riter, ['', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False, True, False])

		self.map.queue_draw()
		self.core.trackManager.saveTracks()

	def onRoutingToggle(self, widget, i):
		self.core.trackManager.routings[int(i)].visible = not self.core.trackManager.routings[int(i)].visible
		self.updateRoutings()
		self.updateTrack()

	def onRoutingNameEdit(self, widget, i, name):
		self.core.trackManager.routings[int(i)].name = utils.uniqueName(name, self.core.trackManager.routings)
		self.updateRoutings()
		