# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""

import json
import logging
import os
import platform
import sys
from datetime import date, datetime

from gweatherrouting import log  # noqa: F401

logger = logging.getLogger("gweatherrouting")


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def app_data_path(appname, roaming=True):  # noqa: C901
    if sys.platform.startswith("java"):
        os_name = platform.java_ver()[3][0]
        if os_name.startswith("Windows"):
            system = "win32"
        elif os_name.startswith("Mac"):
            system = "darwin"
        else:
            system = "linux2"
    else:
        system = sys.platform

    if system == "win32":
        from appdirs import _get_win_folder

        const = roaming and "CSIDL_APPDATA" or "CSIDL_LOCAL_APPDATA"
        path = os.path.normpath(_get_win_folder(const))
        if appname:
            path = os.path.join(path, appname)
    elif system == "darwin":
        path = os.path.expanduser("~/Library/Application Support/")
        if appname:
            path = os.path.join(path, appname)
    elif system == "android":
        path = ""
    elif system == "ios":
        pass
    else:
        path = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/"))
        if appname:
            path = os.path.join(path, "." + appname)
    return path


APP_NAME = "gweatherrouting"
DATA_DIR = app_data_path(appname=APP_NAME)
GRIB_DIR = DATA_DIR + "/grib/"
TEMP_DIR = DATA_DIR + "/temp/"
POLAR_DIR = DATA_DIR + "/polars/"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GRIB_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(POLAR_DIR, exist_ok=True)


class Storage(dict):
    __init = False

    def __init__(self, filename=None, parent=None, *args, **kwargs):
        super(Storage, self).__init__(*args, **kwargs)

        self.__parent = parent
        self.__filename = filename
        self.__handlers = {}

        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

        if parent is not None:
            self.__init = True

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)
        self.save()
        self.notify_change(key, value)

    def __setitem__(self, key, value):
        super(Storage, self).__setitem__(key, value)
        self.__dict__.update({key: value})
        self.save()
        self.notify_change(key, value)

    def __delattr__(self, item):
        self.__delitem__(item)
        self.save()

    def __delitem__(self, key):
        super(Storage, self).__delitem__(key)
        del self.__dict__[key]
        self.save()

    def load_data(self, data):
        for x in data:
            # if isinstance(data[x], dict):
            # 	self[x].load_data(data[x])
            # else:
            self[x] = data[x]

    def save(self):
        if self.__parent:
            return self.__parent.save()

        if not self.__filename or not self.__init:
            return

        with open(DATA_DIR + "/" + self.__filename + ".json", "w") as f:
            f.write(
                json.dumps(
                    self.to_dict(), sort_keys=True, indent=4, default=json_serial
                )
            )
            # logger.debug ('Configuration saved to %s/%s.json' % (DATA_DIR, self.__filename))
            f.close()

    def load(self):
        if self.__parent:
            return

        if not self.__filename:
            return

        with open(DATA_DIR + "/" + self.__filename + ".json", "r") as f:
            j = json.loads(f.read())
            self.load_data(j)
            logger.debug(
                "Load configuration from %s/%s.json", DATA_DIR, self.__filename
            )

    def load_or_save_default(self):
        try:
            self.load()
            self.__init = True
        except:
            self.__init = True
            self.save()

    def to_dict(self):
        d = {}
        for x in self:
            if x.find("Storage") != -1:
                continue

            # check if self[x] has a to_dict method
            # if hasattr(self[x], 'to_dict'):
            # 	# if isinstance(self[x], dict) and
            # 	# d[x] = self[x].to_dict()
            # else:
            d[x] = self[x]

        return d

    def register_on_change(self, k, handler):
        if k not in self.__handlers:
            self.__handlers[k] = []

        self.__handlers[k].append(handler)
        handler(self[k])

    def notify_change(self, k, v):
        if not self.__init:
            return

        if not self.__handlers:
            return

        if k not in self.__handlers:
            return

        for x in self.__handlers[k]:
            x(v)
