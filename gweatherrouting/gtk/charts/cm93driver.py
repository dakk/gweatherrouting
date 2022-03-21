# https://github.com/OpenCPN/OpenCPN/blob/master/src/cm93.cpp

def loadCM93Dictionary(path):
    with open(path, 'r') as f:
        d = f.read().split('\n')
        dd = list(map(lambda x: x.split('|'), d))
        return dict (dd)

class CM93Driver:
    def __init__(self):
        pass 

    def Open(self, path):
        attrDict = loadCM93Dictionary(path + 'CM93ATTR.DIC')
        objDict = loadCM93Dictionary(path + 'CM93OBJ.DIC')
        limitsDict = loadCM93Dictionary(path + 'LIMITS.DIC')

        return None