[app]
title = Priston Tale
package.name = pristontale
package.domain = org.toopen8
source.dir = .
# 리소스 확장자 전수 포함
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = assets/*,images/*

# [핵심] 아이콘 이미지 설정 (보내주신 사진의 icon.png 반영)
icon.filename = icon.png

version = 0.1
requirements = python3,kivy==2.3.0,kivymd,pillow,requests,pyjnius

orientation = portrait
android.archs = arm64-v8a
android.allow_backup = True
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,CAMERA

# 필승 버전 고정
android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
