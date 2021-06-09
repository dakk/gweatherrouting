class CairoStyle:
    def __init__(self, color = None, lineWidth = None, fontSize = None, dash = None):
        self.color = color
        self.lineWidth = lineWidth
        self.fontSize = fontSize
        self.dash = dash

    def apply(self, cr):
        if self.lineWidth: 
            cr.set_line_width(self.lineWidth)
        if self.fontSize:
            cr.set_font_size(self.fontSize)

        if self.dash != None and type(self.dash) == float:
            cr.set_dash([self.dash])
        elif self.dash != None and type(self.dash) != float:
            cr.set_dash(self.dash)
            
        if self.color:
            cr.set_source_rgba (self.color[0], self.color[1], self.color[2], self.color[3])


class Style:
    def resetDash(cr):
        cr.set_dash([])

    class GeoJSON:
        Sea = CairoStyle(color=(0xd3 / 255, 0xdc / 255, 0xa4 / 255, 1.0))
        LandStroke = CairoStyle(color=(0xe7 / 255., 0xdd / 255., 0x1d / 255., 1.0))
        LandFill = CairoStyle(color=(0xe7 / 255., 0xdd / 255., 0x1d / 255., 0.6))

    class Track:
        RoutingTrack = CairoStyle(color=(1,0,0,1), lineWidth=2)
        RoutingTrackFont = CairoStyle(color=(1,1,1,1), fontSize=13)

        TrackActive = CairoStyle(color=(0x91/255., 0x4a/255., 0x7c/255., 1), lineWidth=2, dash=8.0)
        TrackActiveFont = CairoStyle(color=(1,1,1,1), fontSize=13)
        TrackActivePoiFont = CairoStyle(color=(1,1,1,1), fontSize=13)

        TrackInactive = CairoStyle(color=(0x91/255., 0x4a/255., 0x7c/255., 0.6), lineWidth=2, dash=8.0)
        TrackInactiveFont = CairoStyle(color=(1,1,1,0.6), fontSize=13)
        TrackInactivePoiFont = CairoStyle(color=(1,1,1,0.7), fontSize=13)

        RoutingBoat = CairoStyle(color=(0, 0.4, 0, 1.0), lineWidth=5)

    class Poi:
        Triangle = CairoStyle(color=(1, 1, 1, 1))
        Font = CairoStyle(color=(1, 1, 1, 1), fontSize=13)
        