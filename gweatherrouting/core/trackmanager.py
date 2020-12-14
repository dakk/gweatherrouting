from .track import Track 

class TrackManager:
    def __init__(self):
        self.tracks = []
        self.active = None

    def create(self):
        self.tracks.append (Track(name=('noname-%d' % (len(self.tracks) + 1))))
        self.active = len(self.tracks) - 1

    def activeTrack(self):
        if self.active != None:
            return self.tracks[self.active]
        return None 

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