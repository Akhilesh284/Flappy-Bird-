[app]
title = Flappy Bird
package.name = flappybird
package.domain = org.akhilesh
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,wav,mp3,json,txt
version = 1.0
requirements = python3==3.11.8,hostpython3==3.11.8,pygame_sdl2
orientation = portrait
fullscreen = 1

# Android API versions
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# Allow internet permission (safe even if your game doesn't use it)
android.permissions = INTERNET

# Show log while debugging
log_level = 2

# Presplash color
android.presplash_color = #000000

[buildozer]
warn_on_root = 1
