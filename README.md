# peiyin-manager · 配音班表管家（分发版）

已剥离原作者私密配置，只含通用逻辑。安装后首次使用会引导你填自己的配置，并自动固化进 skill 目录；之后每次启动直接读取，**不再重复 Onboarding**。

## 安装
1. 把 `peiyin-manager/` 整个文件夹复制到你的 skills 目录：
   - macOS / Linux：`~/.workbuddy/skills/peiyin-manager/`
   - Windows：`%USERPROFILE%\.workbuddy\skills\peiyin-manager\`
2. 准备 iCloud 通道（详见 `references/icloud-calendar-ops.md`）：
   - 在本机建 `~/dubbing-caldav/`，放入 `scripts/icloud_calendar.py`
   - 建 venv 装依赖：`bin/pip install caldav icalendar`
   - 把 `scripts/icloud_config_template.py` 复制为同目录 `icloud_config.py`，填入你的 Apple ID（手机号加 86 前缀）+ 应用专用密码
3. 授权腾讯文档：安装 `tencent-docs` skill，连接器扫码 OAuth，确保财务表 `policy=0`（仅自己可见）
4. 在对话里说一句"配音班表"，skill 会读本目录的 `peiyin-config.md`：
   - 仍是模板占位符 → 自动进入 Onboarding，逐项收集署名 / 计费 / iCloud / 腾讯文档，并写回 `peiyin-config.md`
   - 之后每次加载读取该配置，**跳过 Onboarding 直接就绪**

## 使用
发一条班表（文字或图片）即可自动完成：冲突检测 → 写 iCloud 日历 → 算费 → 同步腾讯文档财务表。

## 隐私
- 本包不含任何原作者凭证 / 真实数据；你的所有个人信息只存在你本机的 `peiyin-config.md` 与 `icloud_config.py`。
- 填入个人信息后，请勿把 `peiyin-config.md` 或 `icloud_config.py` 分享给他人或提交到公开仓库。

## 许可证
[MIT](LICENSE) © 2026 kamona25 — 可自由使用、修改、分享，作者不对使用后果负责。
