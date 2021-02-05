# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

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



class Config:
    def __init__(self, fn, dc):
        self.fileName = fn
        self.dconf = dc

    def __contains__ (self, key):
        return key in self.dconf 

    def __getitem__ (self, key):
        return self.dconf [key]

    def __setitem__ (self, key, value):
        self.dconf[key] = value
        self.save()

    def save(self):
        with open(DATA_DIR + '/' + self.fileName + '.json', 'w') as f:
            f.write(json.dumps(self.dconf))
            logger.debug ('Configuration saved to %s/%s.json' % (DATA_DIR, self.fileName))
            f.close()
            
    def load(fn):
        try:
            with open(DATA_DIR + '/' + fn + '.json', 'r') as f:
                c = Config(fn, json.loads(f.read()))
                f.close()
                logger.debug ('Load configuration from %s/%s.json' % (DATA_DIR, c.fileName))
                return c
        except:
            c = Config(fn, {})
            c.save()
            return c

        
# A class for objects that contains session data
class Sessionable:
    def __init__(self, filename, default):
        self.fileName = filename 
        self.defaultSession = default
        self.session = {}
        self.loadSession()

    def storeSessionVariable(self, k, v):
        self.session[k] = v
        self.saveSession()
        logger.debug ('Stored session variable \'%s\' to %s/%s.json' % (k, DATA_DIR, self.fileName))

    def getSessionVariable(self, k):
        if k in self.session:
            return self.session[k]
        return None

    def saveSession(self):
        with open(DATA_DIR + '/' + self.fileName + '.json', 'w') as f:
            f.write(json.dumps(self.session))
            # logger.debug ('Configuration saved to %s/%s.json' % (DATA_DIR, self.fileName))
            f.close()

    def loadSession(self):
        try:
            with open(DATA_DIR + '/' + self.fileName + '.json', 'r') as f:
                self.session = json.loads(f.read())
                f.close()
                logger.debug ('Load session file %s/%s.json' % (DATA_DIR, self.fileName))
        except:
            logger.debug ('Creating session file %s/%s.json' % (DATA_DIR, self.fileName))
            self.session = self.defaultSession
            self.saveSession()