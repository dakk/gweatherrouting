"""PyInstaller runtime hook to set GI_TYPELIB_PATH to the bundled typelibs."""
import os
import sys

if hasattr(sys, "_MEIPASS"):
    typelib_path = os.path.join(sys._MEIPASS, "gi_typelibs")
    existing = os.environ.get("GI_TYPELIB_PATH", "")
    if existing:
        os.environ["GI_TYPELIB_PATH"] = typelib_path + ":" + existing
    else:
        os.environ["GI_TYPELIB_PATH"] = typelib_path
