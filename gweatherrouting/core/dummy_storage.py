# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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



APP_NAME = 'gweatherrouting'
DATA_DIR = '/storage'
GRIB_DIR = DATA_DIR
TEMP_DIR = DATA_DIR

class Storage(dict):
    __init = False
    
    def __init__(self, filename = None, parent = None, *args, **kwargs):
        super(Storage, self).__init__(*args, **kwargs)

        self.__parent = parent
        self.__filename = filename
        self.__handlers = {}

        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.iteritems():
                self[k] = v

        if parent != None:
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

    def loadData(self, data):
        for x in data:
            if isinstance(data[x], dict):
                self[x].loadData(data[x])
            else:
                self[x] = data[x]

    def save(self):
        if self.__parent:
            return self.__parent.save()
        
        if not self.__filename or not self.__init:
            return

    def load(self):
        if self.__parent:
            return
            
        if not self.__filename:
            return

        return
            
    def loadOrSaveDefault(self):
        try:
            self.load()
            self.__init = True
        except:
            self.__init = True
            self.save()

    def to_dict(self):
        d = {}
        for x in self:
            if x.find('Storage') != -1:
                continue

            if isinstance(self[x], dict):
                d[x] = self[x].to_dict()
            else:
                d[x] = self[x]

        return d

    def register_on_change(self, k, handler):
        if not (k in self.__handlers):
            self.__handlers[k] = []

        self.__handlers[k].append(handler)
        handler(self[k])

    def notify_change(self, k, v):
        print('notify change', k, v)
        if not self.__init:
            return 

        if not (k in self.__handlers):
            return

        for x in self.__handlers[k]:
            x(v)

