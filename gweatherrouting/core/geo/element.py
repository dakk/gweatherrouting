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
import gpxpy


class Element:
    def __init__(self, name="any", visible=True, collection=None):
        self.name = name
        self.visible = visible
        self.collection = collection

    def toGPXObject(self):
        raise Exception("Not implemented")

    def toJSON(self):
        return {"name": self.name, "visible": self.visible}

    @staticmethod
    def fromJSON(j):
        return Element(name=j["name"], visible=j["visible"])

    def export(self, dest, format="gpx"):
        if format == "gpx":
            gpx = gpxpy.gpx.GPX()

            ob = self.toGPXObject()
            if isinstance(ob, gpxpy.gpx.GPXTrack):
                gpx.tracks.append(ob)
            elif isinstance(ob, gpxpy.gpx.GPXRoute):
                gpx.routes.append(ob)
            elif isinstance(ob, gpxpy.gpx.GPXWaypoint):
                gpx.waypoints.append(ob)

            try:
                f = open(dest, "w")
                f.write(gpx.to_xml())
                f.close()
                return True
            except Exception as e:
                print(str(e))

        return False

    def __len__(self):
        return 0
