[app]
title = PT1 Manager
package.name = pt1manager
package.domain = org.toopen8
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = *
icon.filename = icon.png

version = 0.1
requirements = python3,kivy==2.3.0,kivymd,pillow,requests,pyjnius,android

orientation = portrait
android.archs = arm64-v8a
android.allow_backup = True
# 미디어 접근 권한 강화 (API 34 최적화)
android.permissions = INTERNET, CAMERA, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
