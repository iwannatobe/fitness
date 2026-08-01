[app]

title = Fitness Tracker
package.name = fitnessapp
package.domain = org.fitness

source.dir = .
source.include_exts = py,ttf,wav,atlas,png,jpg,gif,db
source.exclude_patterns = check_pkg.py,ui参考文件/*,tools/*,test_images/*,assets/catalog/gifs/*

version = 2.1

icon.filename = assets/icons/icon.png
presplash.filename = assets/icons/icon.png
presplash.color = #07090B

# iOS: kivy-ios 需要较新的 Kivy（>=2.2 修复新 SDK GL 兼容），用 2.3.1
requirements = python3,kivy==2.3.1,httpx,httpcore,h11,anyio,sniffio,certifi,typing_extensions,idna

orientation = portrait
fullscreen = 1

osx.python_version = 3
osx.kivy_version = 2.3.1

ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.codesign.allowed = false

log_level = 2
storage_dir = /Users/runner/.buildozer

[buildozer]
log_level = 2
warn_on_root = 1
