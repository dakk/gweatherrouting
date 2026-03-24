"""PyInstaller runtime hook to set GI_TYPELIB_PATH and GTK paths on Windows."""

import os
import sys

if hasattr(sys, "_MEIPASS"):
    base = sys._MEIPASS
    # In onedir mode, the exe is in the dist folder; _MEIPASS may be
    # the same dir or an _internal subdir. The manually-copied osgeo/
    # and DLLs live next to the exe.
    exe_dir = os.path.dirname(sys.executable)

    # Add DLL search paths so native extensions (_gdal.pyd etc.) find DLLs
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(base)
        os.add_dll_directory(exe_dir)

    # Prepend to PATH as fallback for DLL loading
    os.environ["PATH"] = exe_dir + ";" + base + ";" + os.environ.get("PATH", "")

    # Add exe_dir to sys.path so manually-copied packages (osgeo/) are importable
    if exe_dir not in sys.path:
        sys.path.insert(0, exe_dir)

    # GObject Introspection typelibs
    for d in (base, exe_dir):
        typelib_path = os.path.join(d, "gi_typelibs")
        if os.path.isdir(typelib_path):
            existing = os.environ.get("GI_TYPELIB_PATH", "")
            if existing:
                os.environ["GI_TYPELIB_PATH"] = typelib_path + ";" + existing
            else:
                os.environ["GI_TYPELIB_PATH"] = typelib_path
            break

    # GDAL data
    for d in (base, exe_dir):
        gdal_data = os.path.join(d, "share", "gdal")
        if os.path.isdir(gdal_data):
            os.environ["GDAL_DATA"] = gdal_data
            break

    # GTK settings for Windows
    os.environ["GTK_DATA_PREFIX"] = exe_dir
    for d in (base, exe_dir):
        loaders = os.path.join(d, "lib", "gdk-pixbuf-2.0", "2.10.0", "loaders.cache")
        if os.path.isfile(loaders):
            os.environ["GDK_PIXBUF_MODULE_FILE"] = loaders
            break
    os.environ["XDG_DATA_DIRS"] = os.path.join(exe_dir, "share")
