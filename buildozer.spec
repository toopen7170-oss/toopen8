[app]
title = ProjectMaster
package.name = toopen8
package.domain = org.toopen7170
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,yml
version = 0.1
requirements = python3,kivy,android,pyjnius

orientation = portrait
fullscreen = 0
android.archs = arm64-v8a

# Android 14 (API 34) 및 NDK r26b 고정
android.api = 34
android.minapi = 21
android.ndk = 26b
android.ndk_path = 
android.sdk_path = 

# 권한 설정
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES

[buildozer]
log_level = 2
warn_on_root = 1
