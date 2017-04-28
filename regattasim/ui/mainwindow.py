import gi
import math

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

from .. import config

UI_INFO = """
<ui>
	<menubar name='MenuBar'>
		<menu action='FileMenu'>
			<menuitem action='FileOpen' />
			<menuitem action='FileSave' />
			<separator />
			<menuitem action='FileQuit' />
		</menu>
	</menubar>
</ui>
"""



class MainWindow(Gtk.Window):
	def __init__(self, core):
		Gtk.Window.__init__ (self, title="Regatta Simulator")
		self.core = core
		self.set_default_size (800, 600)
		self.maximize ()

		box = Gtk.Box (orientation=Gtk.Orientation.VERTICAL)

		# Menu
		action_group = Gtk.ActionGroup ("actions")

		action_filemenu = Gtk.Action ("FileMenu", "File", None, None)
		action_group.add_action(action_filemenu)

		act = Gtk.Action ("FileOpen", None, None, Gtk.STOCK_OPEN)
		act.connect ("activate", self.onOpen)
		action_group.add_action (act)
				
		act = Gtk.Action ("FileSave", None, None, Gtk.STOCK_SAVE)
		act.connect ("activate", self.onQuit)
		action_group.add_action (act)

		act = Gtk.Action ("FileQuit", None, None, Gtk.STOCK_QUIT)
		act.connect ("activate", self.onQuit)
		action_group.add_action (act)

		uimanager = Gtk.UIManager ()
		uimanager.add_ui_from_string (UI_INFO)
		accelgroup = uimanager.get_accel_group ()
		self.add_accel_group (accelgroup)

		uimanager.insert_action_group (action_group)
		self.menubar = uimanager.get_widget ("/MenuBar")

		box.pack_start (self.menubar, False, False, 0)

		### Center
		boxcenter = Gtk.Box (orientation=Gtk.Orientation.HORIZONTAL)
		box.pack_start (boxcenter, True, True, 0)

		## Controls
		boxcontrols = Gtk.Box (orientation=Gtk.Orientation.VERTICAL)
		boxcenter.pack_start (boxcontrols, False, False, 0)

		## Map area
		self.osm = OsmGpsMap.Map () #repo_uri='http://t1.openseamap.org/seamark/#Z/#X/#Y.png', image_format='png')
		self.osm.connect ('button_press_event', self.onMapClick)
		boxcenter.pack_start (self.osm, True, True, 0)

		## Track
		boxtrack = Gtk.Box (orientation=Gtk.Orientation.VERTICAL)
		boxcenter.pack_start (boxtrack, False, False, 0)

		self.trackStore = Gtk.ListStore (int, str, float, float)
		self.trackTree = Gtk.TreeView (self.trackStore)

		renderer = Gtk.CellRendererText ()
		self.trackTree.append_column (Gtk.TreeViewColumn(" ", renderer, text=0))
		self.trackTree.append_column (Gtk.TreeViewColumn("Name", renderer, text=1))
		self.trackTree.append_column (Gtk.TreeViewColumn("Latitude", renderer, text=2))
		self.trackTree.append_column (Gtk.TreeViewColumn("Longitude", renderer, text=3))
		boxtrack.pack_start (self.trackTree, True, True, 0)

		# Track controls
		boxtrackcontrols = Gtk.Box (orientation=Gtk.Orientation.HORIZONTAL)
		boxtrack.pack_start (boxtrackcontrols, False, False, 0)

		button = Gtk.Button.new_from_stock (Gtk.STOCK_GO_UP)
		button.connect ("clicked", self.onWaypointUp)
		boxtrackcontrols.pack_start (button, True, True, 0)

		button = Gtk.Button.new_from_stock (Gtk.STOCK_GO_DOWN)
		button.connect ("clicked", self.onWaypointDown)
		boxtrackcontrols.pack_start (button, True, True, 0)

		button = Gtk.Button.new_from_stock (Gtk.STOCK_REMOVE)
		button.connect ("clicked", self.onWaypointRemove)
		boxtrackcontrols.pack_start (button, True, True, 0)

		boxtrack.pack_start (Gtk.Separator (), False, False, 10)
		
		boxtrack.pack_start (Gtk.Label ('Latitude:'), False, False, 0)
		self.waypointLat = Gtk.Entry ()
		boxtrack.pack_start (self.waypointLat, False, False, 3)
		
		boxtrack.pack_start (Gtk.Label ('Longitude:'), False, False, 0)
		self.waypointLon = Gtk.Entry ()
		boxtrack.pack_start (self.waypointLon, False, False, 3)

		boxtrack.pack_start (Gtk.Label ('Name:'), False, False, 0)
		self.waypointName = Gtk.Entry ()
		boxtrack.pack_start (self.waypointName, False, False, 3)

		button = Gtk.Button.new_with_label ('Insert')
		button.connect ("clicked", self.addWaypoint)
		boxtrack.pack_start (button, False, False, 0)

		# Status bar
		self.statusbar = Gtk.Statusbar ()
		self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Regatta Simulator started')
		box.pack_start (self.statusbar, False, False, 0)

		self.add (box)
		self.show_all ()

		#self.onOpen (self)



	def onOpen (self, widget):
		dialog = Gtk.FileChooserDialog("Please choose a file", self,
					Gtk.FileChooserAction.OPEN,
					(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
			
		filter_py = Gtk.FileFilter()
		filter_py.set_name("GPX track")
		filter_py.add_mime_type("application/gpx+xml")
		dialog.add_filter(filter_py)

		response = dialog.run()
		
		if response == Gtk.ResponseType.OK:
			filepath = dialog.get_filename()
			dialog.destroy()

			if self.core.load (filepath):
				self.updateTrack ()
				edialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done")
				edialog.format_secondary_text ("File opened, loaded %d waypoints" % len (self.core.getTrack ()))
				edialog.run()
				edialog.destroy()	
				self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Loaded %s with %d waypoints' % (filepath, len (self.core.getTrack ())))					
				
			else:
				edialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
				edialog.format_secondary_text ("Cannot open file: %s" % filepath)
				edialog.run()
				edialog.destroy()
		else:
			dialog.destroy()


	def updateTrack (self):
		self.trackStore.clear ()
		self.osm.track_remove_all ()
		track = OsmGpsMap.MapTrack ()

		i = 0
		for wp in self.core.getTrack ():
			i += 1
			self.trackStore.append([i, wp['name'], wp['lat'], wp['lon']])

			p = OsmGpsMap.MapPoint ()
			p.set_degrees (wp['lat'], wp['lon'])
			track.add_point (p)
		self.osm.track_add (track)
		

	def onMapClick (self, osm, event):
		lat, lon = self.osm.get_event_location (event).get_degrees ()
		self.waypointLat.set_text (str (lat))
		self.waypointLon.set_text (str (lon))


	def addWaypoint (self, widget):
		lat = self.waypointLat.get_text ()
		lon = self.waypointLon.get_text ()

		if len (lat) > 1 and len (lon) > 1:
			name = self.waypointName.get_text ()
			self.core.getTrack ().add (float (lat), float (lon), name)
			self.updateTrack ()

			self.waypointLat.set_text ('')
			self.waypointLon.set_text ('')
			self.waypointName.set_text ('')


	def onWaypointDown (self, widget):
		selection = self.trackTree.get_selection ()
		model, treeiter = selection.get_selected ()
		
		if treeiter != None:
			self.core.getTrack ().moveDown (int (model[treeiter][0]) - 1)
			self.updateTrack ()

		
	def onWaypointUp (self, widget):
		selection = self.trackTree.get_selection ()
		model, treeiter = selection.get_selected ()
		
		if treeiter != None:
			self.core.getTrack ().moveUp (int (model[treeiter][0]) - 1)
			self.updateTrack ()

		
	def onWaypointRemove (self, widget):
		selection = self.trackTree.get_selection ()
		model, treeiter = selection.get_selected ()
		
		if treeiter != None:
			self.core.getTrack ().remove (int (model[treeiter][0]) - 1)
			self.updateTrack ()


	def onQuit (self, widget):
		Gtk.main_quit ()


	def dummyClick (self, w):
		pass