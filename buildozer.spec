[app]
title = PristonTale
package.name = pt1
package.domain = org.test

source.dir = .
source.include_exts = py,png,ttf,kv,atlas

version = 1.0

requirements = python3,kivy,kivymd,pillow,requests,plyer

orientation = portrait
fullscreen = 1

android.api = 34
android.minapi = 24
android.archs = arm64-v8a
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

icon.filename = icon.png
presplash.filename = bg.png