[app]

title = PristonTale
package.name = pt1
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,ttf,kv

version = 1.0

requirements = python3,kivy,kivymd,pillow,requests,plyer

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 🔥 안정 고정
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.build_tools_version = 34.0.0

# 🔥 라이선스 자동
android.accept_sdk_license = True

# 🔥 필수 (없으면 오류)
android.sdk_path = /home/runner/android-sdk

# 🔥 이미지 (반드시 파일 있어야 함)
icon.filename = icon.png
presplash.filename = bg.png

[buildozer]
log_level = 2