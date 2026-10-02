[app]
version = 1.0.0
package.name = itsctimer
package.domain = org.itsctimer
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests, bin, venv, .github

# Android 编译版本
android.api = 33
android.ndk = 25b
# android.sdk = 24  # 删除！和api33冲突，交给p4a自动下载
android.minapi = 21

# 打包依赖
requirements = python3,kivy==2.3.1,plyer

title = ITSC Ticket Timer V1
orientation = portrait
fullscreen = 0

# 安卓权限：POST_NOTIFICATIONS仅API33+可用，用:android-maxSdkVersion限定
android.permissions = INTERNET,ACCESS_NETWORK_STATE,VIBRATE
android.permissions += POST_NOTIFICATIONS:android-maxSdkVersion=99:android-minSdkVersion=33

android.release = 0
android.debuggable = 1

# p4a分支，不要用master！master随时可能崩
p4a.branch = develop
p4a.bootstrap = sdl2

# 可选：图标和启动页，把图片放到项目根目录再取消注释
# android.icon = icon.png
# android.presplash = presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
