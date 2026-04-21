[app]
title = Priston Tale
package.name = pristontale
package.domain = org.toopen8

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = *

icon.filename = icon.png

version = 1.0

requirements = python3,kivy==2.2.1,kivymd==1.1.1,pillow,requests,pyjnius

orientation = portrait
android.archs = arm64-v8a

# 🔥 안정 권한만 사용
android.permissions = INTERNET, CAMERA, READ_MEDIA_IMAGES

android.api = 34
android.minapi = 21

android.ndk = 25b
android.ndk_api = 21

android.accept_sdk_license = True
android.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1