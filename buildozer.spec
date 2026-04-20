[app]
# (section) 앱 기본 정보 - 점주님 지시사항 반영
title = Priston Tale
package.name = pristontale
package.domain = org.toopen8

# [중요] 소스 코드와 리소스 포함 설정 (배경/폰트 유실 방지)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = assets/*,images/*

# 앱 버전
version = 0.1

# (section) 라이브러리 의존성
requirements = python3,kivy==2.3.0,kivymd,pillow,requests,pyjnius

# (section) 안드로이드 상세 설정 - 65회차 성공 로직 계승
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.archs = arm64-v8a
android.allow_backup = True

# [권한] 사진 관리 및 인터넷 권한
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,CAMERA

# [SDK/NDK] 필승 버전 고정
android.api = 34
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.skip_update = False

# [부트스트랩]
android.bootstrap = sdl2

# (section) 빌드 환경 설정
[buildozer]
log_level = 2
warn_on_root = 1
