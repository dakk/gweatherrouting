# -*- coding: utf-8 -*-
# Copyright (C) 2017-2026 Davide Gessa
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

# https://github.com/OpenCPN/OpenCPN/blob/master/gui/src/cm93.cpp

import logging
import os

from .cm93datasource import CM93DataSource
from .cm93parser import load_cm93_attr_dictionary, load_cm93_obj_dictionary

logger = logging.getLogger("gweatherrouting")


class CM93Driver:
    def __init__(self):
        pass

    def Open(self, path):  # noqa: N802
        """Open a CM93 chart directory and return a CM93DataSource."""
        if not path.endswith(os.sep):
            path = path + os.sep

        obj_path = os.path.join(path, "CM93OBJ.DIC")
        attr_path = os.path.join(path, "CM93ATTR.DIC")

        if not os.path.exists(obj_path) or not os.path.exists(attr_path):
            logger.error("CM93 dictionary files not found in %s", path)
            return None

        obj_dict, _ = load_cm93_obj_dictionary(obj_path)
        attr_dict, _ = load_cm93_attr_dictionary(attr_path)

        if not obj_dict:
            logger.error("Failed to parse CM93OBJ.DIC")
            return None

        logger.info("Opening CM93 chart at %s (%d objects, %d attributes)",
                     path, len(obj_dict), len(attr_dict))

        return CM93DataSource(path, obj_dict, attr_dict)
