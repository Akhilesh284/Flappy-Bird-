[app]

title = Flappy Bird

package.name = flappybird

package.domain = org.akhilesh

source.dir = .

source.include_exts = py,png,jpg,jpeg,ttf,wav,mp3,json,txt

version = 1.0

requirements = python3,kivy,pygame

orientation = portrait

fullscreen = 1


# Android API versions
android.api = 33
android.sdk = 34
android.ndk = 27b
android.build_tools_version = 34.0.0
android.minapi = 21

# Allow internet permission (safe even if your game doesn't use it)
android.permissions = INTERNET

# Show log while debugging
log_level = 2

# Architecture
android.archs = arm64-v8a, armeabi-v7a

# Don't keep the screen awake
android.wakelock = False

# Presplash color
android.presplash_color = #000000

