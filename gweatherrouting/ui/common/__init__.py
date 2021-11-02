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

def windColor(wspeed):
    color = "0000CC"
    if wspeed >= 0 and wspeed < 2:
        color = "0000CC"
    elif wspeed >= 2 and wspeed < 4:
        color = "0066FF"
    elif wspeed >= 4 and wspeed < 6:
        color = "00FFFF"
    elif wspeed >= 6 and wspeed < 8:
        color = "00FF66"
    elif wspeed >= 8 and wspeed < 10:
        color = "00CC00"
    elif wspeed >= 10 and wspeed < 12:
        color = "66FF33"
    elif wspeed >= 12 and wspeed < 14:
        color = "CCFF33"
    elif wspeed >= 14 and wspeed < 16:
        color = "FFFF66"
    elif wspeed >= 16 and wspeed < 18:
        color = "FFCC00"
    elif wspeed >= 18 and wspeed < 20:
        color = "FF9900"
    elif wspeed >= 20 and wspeed < 22:
        color = "FF6600"
    elif wspeed >= 22 and wspeed < 24:
        color = "FF3300"
    elif wspeed >= 24 and wspeed < 26:
        color = "FF0000"
    elif wspeed >= 26 and wspeed < 28:
        color = "CC6600"
    elif wspeed >= 28:
        color = "CC0000"

    a = int(color[0:2], 16) / 255.0
    b = int(color[2:4], 16) / 255.0
    c = int(color[4:6], 16) / 255.0
    return (a,b,c)