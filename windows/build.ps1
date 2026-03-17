#!/usr/bin/env pwsh
# Windows build script for GWeatherRouting
# Requires: MSYS2 with GTK3, GDAL, GObject Introspection installed
# Run from the repository root: powershell -ExecutionPolicy Bypass -File windows/build.ps1

param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$APP_NAME = "GWeatherRouting"

Write-Host "`n========== GWeatherRouting Windows Build ==========" -ForegroundColor Cyan
Write-Host "Building $APP_NAME for Windows..." -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

# Detect MSYS2 installation
$MSYS2_ROOT = if ($env:MSYS2_ROOT) { $env:MSYS2_ROOT } else { "C:\msys64" }
$MINGW_PREFIX = "$MSYS2_ROOT\mingw64"

if (-not (Test-Path $MINGW_PREFIX)) {
    Write-Host "ERROR: MSYS2 mingw64 not found at $MINGW_PREFIX" -ForegroundColor Red
    Write-Host "Install MSYS2 and run: pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-gdal mingw-w64-x86_64-gobject-introspection" -ForegroundColor Yellow
    exit 1
}

# Add MSYS2 mingw64 bin to PATH
$env:PATH = "$MINGW_PREFIX\bin;$env:PATH"

# Find typelib directory
$TYPELIB_DIR = "$MINGW_PREFIX\lib\girepository-1.0"
if (-not (Test-Path $TYPELIB_DIR)) {
    Write-Host "ERROR: GObject Introspection typelib directory not found at $TYPELIB_DIR" -ForegroundColor Red
    exit 1
}
Write-Host "Found typelib directory: $TYPELIB_DIR" -ForegroundColor Green

# Collect typelib flags for PyInstaller
$REQUIRED_TYPELIBS = @(
    "Gtk-3.0", "Gdk-3.0", "GdkPixbuf-2.0", "Pango-1.0", "PangoCairo-1.0",
    "GObject-2.0", "GLib-2.0", "Gio-2.0", "cairo-1.0", "Atk-1.0",
    "HarfBuzz-0.0", "freetype2-2.0", "GModule-2.0", "GdkWin32-3.0"
)

$typelibFlags = @()
foreach ($typelib in $REQUIRED_TYPELIBS) {
    $typelibFile = "$TYPELIB_DIR\${typelib}.typelib"
    if (Test-Path $typelibFile) {
        $typelibFlags += "--add-data"
        $typelibFlags += "${typelibFile};gi_typelibs"
    } else {
        Write-Host "WARNING: ${typelib}.typelib not found" -ForegroundColor Yellow
    }
}

# Find GDAL data directory
$GDAL_DATA = "$MINGW_PREFIX\share\gdal"
$gdalDataFlags = @()
if (Test-Path $GDAL_DATA) {
    $gdalDataFlags = @("--add-data", "${GDAL_DATA};share/gdal")
    Write-Host "Found GDAL data: $GDAL_DATA" -ForegroundColor Green
} else {
    Write-Host "WARNING: GDAL data directory not found" -ForegroundColor Yellow
}

# Build with PyInstaller
Write-Host "`nRunning PyInstaller..." -ForegroundColor Cyan
Push-Location gweatherrouting

$pyinstallerArgs = @(
    "--name", $APP_NAME,
    "--windowed",
    "--icon", "..\windows\icon.ico",
    "--hidden-import=gi",
    "--collect-submodules=gi",
    "--add-data", "data;gweatherrouting/data",
    "--add-data", "gtk;gweatherrouting/gtk",
    "--runtime-hook", "..\windows\pyinstaller_gi_hook_win.py"
) + $typelibFlags + $gdalDataFlags + @("__main__.py")

pyinstaller @pyinstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# Copy additional GTK runtime files needed on Windows
Write-Host "`nCopying GTK runtime files..." -ForegroundColor Cyan
$distDir = "gweatherrouting\dist\$APP_NAME"

# Copy GTK schemas, icons, and theme data
$gtkDirs = @(
    @("$MINGW_PREFIX\share\glib-2.0\schemas", "$distDir\share\glib-2.0\schemas"),
    @("$MINGW_PREFIX\share\icons\Adwaita", "$distDir\share\icons\Adwaita"),
    @("$MINGW_PREFIX\share\icons\hicolor", "$distDir\share\icons\hicolor"),
    @("$MINGW_PREFIX\lib\gdk-pixbuf-2.0", "$distDir\lib\gdk-pixbuf-2.0")
)

foreach ($dirPair in $gtkDirs) {
    $src = $dirPair[0]
    $dst = $dirPair[1]
    if (Test-Path $src) {
        Write-Host "Copying $src -> $dst"
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Copy-Item -Recurse -Force "$src\*" $dst
    }
}

# Copy GDAL shared data
if (Test-Path $GDAL_DATA) {
    $gdalDst = "$distDir\share\gdal"
    New-Item -ItemType Directory -Force -Path $gdalDst | Out-Null
    Copy-Item -Recurse -Force "$GDAL_DATA\*" $gdalDst
}

Write-Host "`nBuild completed! Output: gweatherrouting\dist\$APP_NAME\" -ForegroundColor Green

# Create installer with Inno Setup if available and not skipped
if (-not $SkipInstaller) {
    $innoCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $innoCompiler) {
        Write-Host "`nCreating installer with Inno Setup..." -ForegroundColor Cyan
        & $innoCompiler "windows\installer.iss"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installer created successfully!" -ForegroundColor Green
        } else {
            Write-Host "WARNING: Inno Setup failed" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`nInno Setup not found, skipping installer creation." -ForegroundColor Yellow
        Write-Host "Install from: https://jrsoftware.org/isinfo.php" -ForegroundColor Yellow
    }
}
