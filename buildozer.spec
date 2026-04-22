[app]

title = PristonTale
package.name = pt1
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

# 🔥 안정 조합
requirements = python3,kivy,requests,plyer

orientation = portrait
fullscreen = 1

# 🔥 완전 고정 (핵심)
android.api = 33
android.minapi = 24
android.ndk = 25b
android.build_tools_version = 33.0.2
android.archs = arm64-v8a

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

log_level = 2