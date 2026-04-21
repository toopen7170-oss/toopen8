[app]
title = Priston Tale
package.name = pristontale
package.domain = org.toopen8

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = *

# [점주님 지시] 아이콘 파일 설정 유지
icon.filename = icon.png

version = 1.0

# [수정] 최신 안드로이드 14 대응을 위해 라이브러리 버전 소폭 조정
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,requests,pyjnius,android

orientation = portrait
android.archs = arm64-v8a

# [보강] 안드로이드 14 미디어 접근 및 필수 권한
android.permissions = INTERNET, CAMERA, READ_MEDIA_IMAGES, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

android.api = 34
android.minapi = 21

# [안정화] NDK 및 SDK 설정 고정
android.ndk = 25b
android.ndk_api = 21

android.accept_sdk_license = True

# [오류 해결] bootstrap 명칭 변경 (deprecated 경고 해결)
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
