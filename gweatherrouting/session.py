import os
import sys
import platform
import logging
import json
from . import log

logger = logging.getLogger ('gweatherrouting')


def app_data_path (appname, roaming=True):
	if sys.platform.startswith('java'):
		os_name = platform.java_ver()[3][0]
		if os_name.startswith('Windows'):
			system = 'win32'
		elif os_name.startswith('Mac'):
			system = 'darwin'
		else:
			system = 'linux2'
	else:
		system = sys.platform

	if system == "win32":
		if appauthor is None:
			appauthor = appname
		const = roaming and "CSIDL_APPDATA" or "CSIDL_LOCAL_APPDATA"
		path = os.path.normpath(_get_win_folder(const))
		if appname:
			path = os.path.join(path, appname)
	elif system == 'darwin':
		path = os.path.expanduser('~/Library/Application Support/')
		if appname:
			path = os.path.join(path, appname)
	else:
		path = os.getenv('XDG_DATA_HOME', os.path.expanduser("~/"))
		if appname:
			path = os.path.join(path, '.'+appname)
	return path


APP_NAME = 'gweatherrouting'
DATA_DIR = app_data_path (appname=APP_NAME)
GRIB_DIR = DATA_DIR + '/grib/'
TEMP_DIR = DATA_DIR + '/temp/'

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GRIB_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


EMPTY_CONF = {
    'grib_loaded': []
}

class Config:
    def __init__(self, dc):
        self.dconf = dc

    def getv(self, key, failsafe=True):
        if key in self.dconf:
            return self.dconf[key]
        return None 

    def setv(self, key, value):
        self.dconf[key] = value
        self.save()

    def save(self):
        with open(DATA_DIR + '/config.json', 'w') as f:
            f.write(json.dumps(self.dconf))
            logger.debug ('Configuration saved to %s/config.json' % DATA_DIR)
            f.close()
            
    def load():
        try:
            with open(DATA_DIR + '/config.json', 'r') as f:
                c = Config(json.loads(f.read()))
                f.close()
                logger.debug ('Load configuration from %s/config.json' % DATA_DIR)
                return c
        except:
            c = Config(EMPTY_CONF)
            c.save()
            logger.debug ('Saved initial configuration to %s/config.json' % DATA_DIR)
            return c

        