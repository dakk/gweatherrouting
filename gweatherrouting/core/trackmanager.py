from .track import Track 

class TrackManager:
    def __init__(self):
        self.tracks = []
        self.activeTrack = None

    def activate(self, name):
        for x in self.tracks:
            if x.name == name:
                self.activeTrack = x
                return 

    def create(self):
        nt = Track(name=('noname-%d' % (len(self.tracks) + 1)))
        nt.clear()
        self.tracks.append (nt)
        self.activeTrack = nt

    def remove(self, i):
        pass 


    def importTrack (self, path):
        try:
            tree = ElementTree.parse (path)
        except:
            return False

        waypoints = []
        root = tree.getroot ()
        for child in root:
            wp = (float (child.attrib['lat']), float (child.attrib['lon']))
            waypoints.append (wp)

        self.tracks.append(Track(path.split('/')[-1].split('.')[0], waypoints))
        return True