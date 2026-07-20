[app]
title = Flappy Bird
package.name = flappybird
package.domain = org.akhilesh
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,wav,mp3,json,txt
version = 1.0
requirements = python3,pygame_sdl2,cython
orientation = portrait
fullscreen = 1

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.permissions = INTERNET
android.presplash_color = #000000

log_level = 2

[buildozer]
warn_on_root = 1
