# iCloud 日历写入命令

## 安全配置原则
- 不得在聊天中要求使用者发送 Apple ID 应用专用密码，也不得在回复或日志中回显凭证。
- 引导使用者在 Apple ID 官网生成应用专用密码，并仅保存到本机 `icloud_config.py` 的现有配置位；对话中只确认“已配置/未配置”。
- 首次配置后先运行只读的 `query` 做连接检查。只有使用者确认测试内容后，才执行 `create`。
- 若工作区已有可用配置，不覆盖、不迁移，也不重复索取凭证。

## 本机准备（首次安装 skill 后）
1. 建目录并放入脚本：在你本机新建一个文件夹（如 `~/dubbing-caldav/`），把本 skill 的 `scripts/icloud_calendar.py` 复制进去。
2. 建 venv 并装依赖：
   - Windows：`cd 该目录` → `python -m venv .` → `Scripts\pip install caldav icalendar tzdata`
   - macOS/Linux：`cd 该目录` → `python3 -m venv .` → `bin/pip install caldav icalendar`
3. 填配置：把 `scripts/icloud_config_template.py` 复制为同目录的 `icloud_config.py`，按注释填入你的 Apple ID（手机号加 86 前缀）、iCloud 应用专用密码、日历名。
4. 此目录即为你的 `<ICLOUD_VENV>`，Onboarding 第5步确认后即可用 `PY="<ICLOUD_VENV>/Scripts/python.exe" CAL="<ICLOUD_VENV>/icloud_calendar.py"` 调用（macOS/Linux 用 `bin/python`）。
5. ⚠️ `icloud_config.py` 含你的凭证，切勿外传 / 上传公开仓库。

脚本：`<ICLOUD_VENV>/icloud_calendar.py`（随本 skill 附在 `scripts/` 子目录，复制到你本机目录即可）
解释器：`<ICLOUD_VENV>/Scripts/python.exe`（Windows）/ `<ICLOUD_VENV>/bin/python`（macOS/Linux）
日历名：「配音班表」　时区：Asia/Shanghai

## 命令全集
```bash
# <ICLOUD_VENV> = 你本机放脚本的 venv 目录（Onboarding 第5步确认）
PY="<ICLOUD_VENV>/Scripts/python.exe"
CAL="<ICLOUD_VENV>/icloud_calendar.py"

# 写入一条班表
$PY $CAL create "配音-作品名" 2026-07-26 14:00 16:00 --loc "地点" --desc "角色｜折合句数｜导演"

# 冲突检测（±7天，比标题+起止时间）
$PY $CAL conflict-check 2026-07-26 14:00 16:00

# 查询（日期范围，精简输出标题+时间+地点）
$PY $CAL query 2026-07-26 2026-08-01

# 搜索（改/取消前先定位 uid）
$PY $CAL search "作品名"

# 删除（用 search 拿到的 uid）
$PY $CAL delete <uid>

# 按作品名批量删
$PY $CAL delete-by-keyword "作品名"
```

## 规范要点
- 标题统一前缀「配音-」，便于搜索与去重
- `--desc` 只写角色 / 折合句数 / 导演；**费用不写进日历**，费用只进腾讯文档财务表
- 改/取消走口语指令：search 拿 uid → delete，或重建新时段
- delete 内部走 search 取正确 ETag，避免 412 冲突
