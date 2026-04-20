[app]
title = Priston Tale
package.name = pristontale
package.domain = org.toopen8
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
# 리소스가 같은 폴더에 있으므로 패턴을 단순화하여 유실 방지
source.include_patterns = *

icon.filename = icon.png

version = 0.1
# android 라이브러리 추가하여 권한 및 시스템 제어 안정화
requirements = python3,kivy==2.3.0,kivymd,pillow,requests,pyjnius,android

orientation = portrait
android.archs = arm64-v8a
android.allow_backup = True

# 최신 안드로이드 보안 가이드에 맞춘 권한 수정
android.permissions = INTERNET, CAMERA, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
