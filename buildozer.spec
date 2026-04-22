[app]

title = PristonTale
package.name = pt1
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

# 🔥 안정 조합 (절대 안 터짐)
requirements = python3,kivy,requests,plyer

orientation = portrait
fullscreen = 1

# 🔥 안정 고정값
android.api = 33
android.minapi = 24
android.ndk = 25b
android.build_tools_version = 33.0.2
android.archs = arm64-v8a

# 권한
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# 로그
log_level = 2