[app]
title = PristonTale
package.name = pt1
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,ttf

version = 1.0

requirements = python3,kivy,kivymd,pillow,requests,plyer

orientation = portrait
fullscreen = 1

# 🔥 안정 고정
android.api = 33
android.minapi = 24
android.ndk = 25b
android.build_tools_version = 33.0.2
android.archs = arm64-v8a

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# ✅ 아이콘 & 배경 다시 추가
icon.filename = icon.png
presplash.filename = bg.png

[buildozer]
log_level = 2