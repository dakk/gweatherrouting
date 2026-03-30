Quickstart
====================================

Installation
------------

The recommended way to install GWeatherRouting is via **Flatpak** from Flathub:

```
flatpak install flathub org.gweatherrouting.gweatherrouting
```

Once installed, you can run it with:

```
flatpak run org.gweatherrouting.gweatherrouting
```

You can also browse the app page on [Flathub](https://flathub.org/apps/org.gweatherrouting.gweatherrouting).

### Alternative: AppImage

You can download the latest AppImage from [GitHub releases](https://github.com/dakk/gweatherrouting/releases). After downloading, make it executable:

```
chmod +x GWeatherRouting-linux-x86_64.AppImage
```

<img src="../_static/images/quickstart/1.png">

### Alternative: Windows

Download the latest [Windows portable ZIP](https://github.com/dakk/gweatherrouting/releases/download/v0.3.6/GWeatherRouting-win64.zip), extract it, and run `GWeatherRouting.bat` (or `GWeatherRouting-noconsole.vbs` to hide the console window).

### Alternative: From source

You can install gweatherrouting from source, following the instructions in the repository [README.md](https://github.com/dakk/gweatherrouting).


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