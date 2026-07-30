"""iCloud CalDAV 配置模板
=================================
使用前：
  1. 复制本文件，改名为 `icloud_config.py`（必须同目录，脚本会 import 它）
  2. 把下面的占位值换成你自己的
  3. 此文件含你的 iCloud 凭证，切勿发给别人 / 上传到公开仓库
"""

# ---- CalDAV 连接 ----
CALDAV_URL = "https://caldav.icloud.com/"
# Apple ID 是手机号时，用户名需加 86 前缀、不带 + 号；
# 带 + 或不加前缀都会 401 认证失败。
USERNAME = "86你的手机号"
# iCloud「应用专用密码」（在 appleid.apple.com → 登录与安全 → 应用专用密码 生成）
# ⚠️ 不是你的 Apple ID 登录密码
PASSWORD = "你的应用专用密码"

# ---- 配音班表日历 ----
DUBBING_CALENDAR_NAME = "配音班表"
# 可选：iCloud 网页版点开该日历后，地址栏里的日历 URL。
# 留空 "" 则按上面名称自动查找（推荐先留空）。
DUBBING_CALENDAR_URL = ""

# ---- 时区 ----
TIMEZONE = "Asia/Shanghai"
