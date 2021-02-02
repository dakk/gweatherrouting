# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
# Copyright (C) 2012 Riccardo Apolloni
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

import math


def cfbinomiale(n,i):
    return math.factorial(n)/(math.factorial(n-i)*math.factorial(i))

class Beizer:
    def __init__(self, points = []):
        self.points = points

    def value (self, t):
        #rende il punto della curva di bezier di parametro t
        n = len(self.points) - 1
        x = 0
        y = 0
        for k in range(0, n+1):
            weight = ((1 - t) ** (n - k)) * (t ** k) * cfbinomiale(n, k)
            x += self.points[k][0] * weight
            y += self.points[k][1] * weight
        return (x, y)