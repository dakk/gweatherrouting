from xml.etree import ElementTree

class Track:
    def __init__ (self):
        self.waypoints = []

    def __len__ (self):
        return len (self.waypoints)

    def __getitem__ (self, key):
        return self.waypoints [key]

    def clear (self):
        self.waypoints = []

    def load (self, path):
        try:
            tree = ElementTree.parse (path)
        except:
            return False

        self.waypoints = []
        root = tree.getroot ()
        for child in root:
            wp = {
                'lat': float (child.attrib['lat']),
                'lon': float (child.attrib['lon']),
                'name': ''
            }

            if len (child.findall('name')) != 0:
                wp['name'] = child.findall('name')[0].text

            self.waypoints.append (wp)

        return True

    def save (self, path):
        return False

    def moveUp (self, i):
        if i > 0 and i < len (self):
            sw = self.waypoints [i-1]
            self.waypoints [i-1] = self.waypoints [i]
            self.waypoints [i] = sw

    def moveDown (self, i):
        if i < len (self) - 1 and i >= 0:
            sw = self.waypoints [i+1]
            self.waypoints [i+1] = self.waypoints [i]
            self.waypoints [i] = sw

    def remove (self, i):
        if i > 0 and i < len (self):
            del self.waypoints [i]

    def add (self, lat, lon, name):
        self.waypoints.append ({
            'lat': lat,
            'lon': lon,
            'name': name
        })