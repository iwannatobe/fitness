[app]

title = Fitness Tracker
package.name = fitnessapp
package.domain = org.fitness

source.dir = .
source.include_exts = py,ttf,wav,atlas,png,gif

version = 1.6

icon.filename = assets/icons/icon.png
presplash.filename = assets/icons/icon.png
presplash.color = #12141A

# Kivy 2.1.0 + p4a v2023.09.16 — proven stable combo for Android
requirements = python3,kivy==2.1.0,httpx,httpcore,h11,anyio,sniffio,certifi,typing_extensions,idna
p4a.branch = v2023.09.16

orientation = portrait
fullscreen = 1

osx.python_version = 3
osx.kivy_version = 2.1.0

android.permissions = VIBRATE, INTERNET, READ_EXTERNAL_STORAGE, RECORD_AUDIO
android.archs = arm64-v8a
android.api = 31
android.minapi = 26
android.ndk = 25b
android.enable_androidx = True
android.entrypoint = org.kivy.android.PythonActivity

ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.codesign.allowed = false

log_level = 1
storage_dir = /home/skaven/buildozer_build

[buildozer]
log_level = 2
warn_on_root = 1
