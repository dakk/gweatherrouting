"""PyInstaller runtime hook to set GI_TYPELIB_PATH and GTK paths on Windows."""
import os
import sys

if hasattr(sys, "_MEIPASS"):
    base = sys._MEIPASS

    # Add DLL search path so native extensions (_gdal.pyd etc.) can find DLLs
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(base)

    # Also prepend to PATH as fallback
    os.environ["PATH"] = base + ";" + os.environ.get("PATH", "")

    # GObject Introspection typelibs
    typelib_path = os.path.join(base, "gi_typelibs")
    existing = os.environ.get("GI_TYPELIB_PATH", "")
    if existing:
        os.environ["GI_TYPELIB_PATH"] = typelib_path + ";" + existing
    else:
        os.environ["GI_TYPELIB_PATH"] = typelib_path

    # GDAL data
    gdal_data = os.path.join(base, "share", "gdal")
    if os.path.isdir(gdal_data):
        os.environ["GDAL_DATA"] = gdal_data

    # GTK settings for Windows
    os.environ["GTK_DATA_PREFIX"] = base
    os.environ["GDK_PIXBUF_MODULE_FILE"] = os.path.join(
        base, "lib", "gdk-pixbuf-2.0", "2.10.0", "loaders.cache"
    )
    os.environ["XDG_DATA_DIRS"] = os.path.join(base, "share")
