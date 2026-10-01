[app]
package.name = itsctimer
package.domain = org.itsctimer
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests, bin, venv, .github

android.api = 33
android.ndk = 25b
android.sdk = 24
android.minapi = 21

# 打包依赖，kivy + plyer（用于通知、震动）
requirements = python3,kivy==2.3.0,plyer==2.1.0

title = ITSC Ticket Timer V1
orientation = portrait
fullscreen = 0

# 安卓权限：通知、震动、网络
android.permissions = INTERNET,ACCESS_NETWORK_STATE,VIBRATE,POST_NOTIFICATIONS

android.release = 0
android.debuggable = 1

p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1

