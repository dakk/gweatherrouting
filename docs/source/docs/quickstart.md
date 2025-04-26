Quickstart
====================================

Installation
------------

Download the latest release appimage from [github releases](https://github.com/dakk/gweatherrouting/releases).
At the moment we only offer an appimage build for linux x86_64, but we will provide soon builds for other systems.

<img src="../_static/images/quickstart/1.png">

You can install gweatherrouting from source source, following the instructions that you can find in the repository [README.md](https://github.com/dakk/gweatherrouting).

After downloading the appimage, make it executable:

```
chmod +x GWeatherRouting-linux-x86_64.AppImage
```


First run
---------

During the first run, gww will ask you to download some files:
- Base world countourn lines
- OpenSeaMap data: contains lighthouses, buoys, and other maritime signals taken from the [openseamap project](https://openseamap.org/index.php?id=openseamap&no_cache=1)

<img src="../_static/images/quickstart/2.png">

After these download, gww is ready to be used.


<img src="../_static/images/quickstart/3.png">


Downloading a grib file
-----------------------

1. Click on the grib manager button

<img src="../_static/images/quickstart/4.png">

2. Select a region, right-click and download 

<img src="../_static/images/quickstart/5.png">

3. After closing the grib manager, the grib file is loaded into the map. You can freely inspect the wind for different time slots.

<img src="../_static/images/quickstart/6.gif">



Track creation and editing
--------------------------

To create a track and add a point to it, right-click in a point of the map and press "Add to Track". This
will create a new track, adding the clicked point to it.

<img src="../_static/images/quickstart/7.png">

In order to add new track points, right-click on another point of the map and press "Add to Track" as before.
On the left pane, you will se the list of the tracks, and the list of track point for each track. 
You can:
- Remove or Export tracks, by right-clicking on a track
- Remove, Reorder or Duplicate a track point, by right-clicking on a track point


<img src="../_static/images/quickstart/8.png">


Create a routing
----------------

Now that we have a track and a grib, creating a routing is very easy. Just click on "Route..." button.
Select a polar file, tune other settings and press run.

<img src="../_static/images/quickstart/9.png">

The software will calculate the isochrones tree, finding the fastest route. After calculation, the route is displayed in red.
The green point on the routing shows the boat position at different times. You can navigate the simulation through time, using
time control's buttons.


<img src="../_static/images/quickstart/10.gif">