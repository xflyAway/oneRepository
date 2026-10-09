# Buildozer 打包配置 —— 房屋收租管理（安卓 APK）
# 由 GitHub Actions 云端构建使用，无需本地执行 buildozer init

[app]

# 应用显示名（安卓桌面上看到的名称）
title = 房屋收租管理

# 包名必须为 ASCII（安卓规范），不能写中文
package.name = rentmanager
package.domain = org.rentapp

# 源码目录与包含的文件类型
# 注意：必须包含 otf，否则中文字体不会打进 APK
source.dir = .
source.include_exts = py,kv,otf,png

# 应用版本
version = 1.0

# 依赖（只内置控件，不需要第三方库）
requirements = python3,kivy==2.3.0

# 竖屏
orientation = portrait
fullscreen = 0

# 权限：本应用只读写应用私有目录，无需任何权限
android.permissions =

# Android 目标平台
android.api = 34
android.minapi = 21
android.ndk = 25b
# 只打 64 位，构建时间减半（现代手机都支持）
android.archs = arm64-v8a

# CI 环境必须自动接受 SDK 许可，否则构建卡在 yes/no 交互
android.accept_sdk_license = True

# 允许系统备份应用数据
android.allow_backup = True

# 保留 Python 输出日志便于排查问题
android.logcat_on_crash = True

[buildozer]

# 构建日志级别
log_level = 2

# 构建输出目录
bin_dir = ./bin

# 构建缓存目录（建议加入 .gitignore）
build_dir = ./.buildozer

warn_on_root = 1
