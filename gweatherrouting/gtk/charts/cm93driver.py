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
# https://github.com/OpenCPN/OpenCPN/blob/master/src/cm93.cpp


def load_cm93_dictionary(path):
    with open(path, "r") as f:
        d = f.read().split("\n")
        dd = list(map(lambda x: x.split("|"), d))
        return dict(dd)


class CM93Driver:
    def __init__(self):
        return

    def Open(self, path):  # noqa: N802
        attr_dict = load_cm93_dictionary(path + "CM93ATTR.DIC")  # noqa: F841
        obj_dict = load_cm93_dictionary(path + "CM93OBJ.DIC")  # noqa: F841
        limits_dict = load_cm93_dictionary(path + "LIMITS.DIC")  # noqa: F841

        return None
