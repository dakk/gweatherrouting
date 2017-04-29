import gi
import math

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

class GribMapLayer (GObject.GObject, OsmGpsMap.MapLayer):
    def __init__ (self, grib):
        GObject.GObject.__init__ (self)
        self.grib = grib

    def drawWindArrow (self, cr, x, y, wdir, wspeed):
        if wspeed < 1.0:
            cr.set_source_rgb (0.,1.,0.)
        elif wspeed < 4.0:
            cr.set_source_rgb (0.5,0.5,0.)
        else:
            cr.set_source_rgb (1.,0.,0.)

        cr.move_to (x, y)
        cr.line_to (x + (wspeed / 2 * math.sin (wdir)), y + 1 * math.cos (wdir))
        cr.line_to (x + (5 + wspeed * math.sin (wdir)), y + (5 + wspeed * math.cos (wdir)))
        cr.stroke ()

    def do_draw (self, gpsmap, cr):
        # Draw boat
        cr.set_line_width (1)
        cr.set_source_rgb (1,0,0)

        for x in range (0, 100):
            for y in range (0, 100):
                w = self.grib.getWind (0, x, y)
                self.drawWindArrow (cr, x * 20, y * 20, w[0], w[1])

    def do_render (self, gpsmap):
        pass

    def do_busy (self):
        return False

    def do_button_press (self, gpsmap, gdkeventbutton):
        return False

GObject.type_register (GribMapLayer)