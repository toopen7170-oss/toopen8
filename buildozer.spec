[app]

title = PristonTale
package.name = pt1
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

requirements = python3,kivy,kivymd,pillow,requests,plyer,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 🔥 핵심 안정 고정
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.build_tools_version = 34.0.0

# 🔥 라이선스 자동 수락
android.accept_sdk_license = True

# 🔥 아이콘/배경
icon.filename = icon.png
presplash.filename = bg.png

# 로그
log_level = 2