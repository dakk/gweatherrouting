class IsoTree:
    def __init__ (self, data, angle):
        self.childs = {}
        self.data = data
        self.angle = angle

    def data (self):
        return (self.data, self.angle)

    def __getitem__ (self, key):
        return self.childs [key]


# Testing
if __name__ == "__main__":
    it = IsoTree ([12], 0.0)

    dt, a = it.data ()
    for x in dt:
        it[x['angle']] = IsoTree (calcola (x['angle']), x['angle'])

