# Gweatherrouting Mobile

Mobile version is far from behind useful. Currently we are experimenting with kivy framework, and we're able to create a working APK with a map. 

![Mobile](https://github.com/dakk/gweatherrouting/raw/master/media/mobile.png)

## Building for android

Install buildozer:

```
git clone https://github.com/kivy/buildozer.git
cd buildozer
sudo python setup.py install
```


Create an apk:

```
rm -rf .buildozer/android/platform/build-armeabi-v7a/build/python-installs/gweatherrouting/gweatherrouting* && buildozer android debug deploy run && buildozer android logcat | grep python
```