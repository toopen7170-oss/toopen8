[app]
title = PristonTale
package.name = pristontale
package.domain = org.toopen7170
source.dir = .
source.include_exts = py,png,jpg,ttf,yml
version = 0.1
requirements = python3,kivy==2.3.0,android,pyjnius

orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
icon.filename = icon.png

android.api = 34
android.minapi = 21
android.ndk = 26b
android.accept_sdk_license = True
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES

[buildozer]
log_level = 2
warn_on_root = 1
