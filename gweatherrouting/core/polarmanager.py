import logging
import os
import shutil
from shutil import copyfile
from typing import Dict, List


from gweatherrouting.core.storage import POLAR_DIR, Storage

logger = logging.getLogger("gweatherrouting")


class PolarManager():
    def __init__(self):
        self.polar_files = None

        self.polars = []

        self.local_polar = []
        self.refresh_local_polars()

    def refresh_local_polars(self):
        self.local_polars = os.listdir(POLAR_DIR)


    def change_state(self, name, state):
        if not state:
            self.disable(name)
        else:
            self.enable(name)

    def enable(self, name):
        self.load(POLAR_DIR + "/" + name)
        self.store_opened_polars()

    def disable(self, name):
        for x in self.polars:
            if x.name == name:
                self.gribs.remove(x)
                self.store_opened_polars()

    def is_enabled(self, name) -> bool:
        for x in self.polars:
            if x.name == name:
                return True
        return False

    def remove(self, name):
        if self.is_enabled(name):
            self.disable(name)
        os.remove(POLAR_DIR + "/" + name)

    def import_polar(self, path):
        polar_filename = os.path.basename(path)
        target_filepath = os.path.join(POLAR_DIR, polar_filename)
        shutil.copyfile(path, target_filepath)
        self.polars.append(polar_filename)
