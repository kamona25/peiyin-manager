# 腾讯文档财务表操作规范

财务数据只维护在腾讯文档在线表格，**不写入日历 desc**。

## 前置
- 已安装 `tencent-docs` skill 并授权连接器（见 SKILL.md 一·B）
- 拿到 `file_id`（建表返回，或使用者提供）
- 新建财务表后先用 `manage.get_privilege` 确认 `policy=0`（仅自己可见）；不满足时不得写入真实财务数据
- 试运行数据必须在“备注”或“项目类型”中明确标注“测试”，并在写入前获得使用者确认

## 0. 实际调用方式（WorkBuddy 内置 tencent-docs skill，非 mcporter）
先用 Skill 工具加载 `tencent-docs`，cd 到其 base 目录后用 `tencentdocs.py` 调用：
```bash
cd "<tencent-docs skill base目录>"   # Skill 加载时会给出
python3 tencentdocs.py tdoc_init                       # 应输出 READY
python3 tencentdocs.py tdoc_call <service> <tool> '<json_args>'
```
- 管理类（建表/搜索/权限）走 service `tencent-docs`，工具名带 `manage.` 前缀
- 表格读写走 service `sheet-mcp`，工具名**不带** `sheet.` 前缀（如 `get_sheet_info` / `set_range_value` / `get_cell_data`）
- 调用前先 `tdoc_schema <service> <tool>` 查参数，勿凭记忆猜

## 1. 建表 / 找表
```bash
# 已有表：按标题搜索拿 file_id
python3 tencentdocs.py tdoc_call tencent-docs manage.search_file '{"search_key":"财务"}'
# 新建表
python3 tencentdocs.py tdoc_call tencent-docs manage.create_file '{"file_type":"sheet","title":"配音财务表"}'
```
返回 `file_id`（和 `url`），**不含 sheet_id**。再调一次拿到默认表的 sheet_id：
```bash
python3 tencentdocs.py tdoc_call sheet-mcp get_sheet_info '{"file_id":"<FILE_ID>"}'
```
返回 `sheets[0].sheet_id`（新表默认即 `BB08J2`），记下来后续用。

## 2. 写数据：set_range_value
`values` 是**对象数组**，每个元素描述一个单元格：
- `row` / `col`：**0-based**
- `value_type`：`STRING` 或 `NUMBER`
- `string_value`（STRING 时必填）/ `number_value`（NUMBER 时必填）

```bash
python3 tencentdocs.py tdoc_call sheet-mcp set_range_value '{
  "file_id":"<FILE_ID>",
  "sheet_id":"<SHEET_ID>",
  "values":[
    {"row":0,"col":0,"value_type":"STRING","string_value":"日期"},
    {"row":1,"col":0,"value_type":"STRING","string_value":"2026-07-26"},
    {"row":1,"col":4,"value_type":"NUMBER","number_value":20},
    {"row":1,"col":5,"value_type":"NUMBER","number_value":1250}
  ]
}'
```
- 一次调用可写多行多列，把所有单元格放进 `values` 数组即可（批量写入）。
- 写完用第 3 步验证是否真正落表。

## 3. 读验证：get_cell_data（必须这样读）
```bash
python3 tencentdocs.py tdoc_call sheet-mcp get_cell_data '{
  "file_id":"<FILE_ID>",
  "sheet_id":"<SHEET_ID>",
  "start_row":0,"end_row":10,
  "start_col":0,"end_col":10,
  "return_csv":true
}'
```
- 参数：`start_row` / `end_row` / `start_col` / `end_col`（**0-based**）
- `return_csv:true` → 返回 `csv_data` 字符串；`false` → 返回 `cells` 结构化数组
- ⚠️ 该工具**没有 `range` 参数**，不要传 `range:"A1:J10"`（该参数不存在，会被忽略，导致只读回首单元格）

## 4. 可选操作
- 冻结首行：`sheet.set_freeze`（row_index=1）
- 查权限：`manage.get_privilege` 确认 policy=0（仅自己可见）

## 5. 推荐字段（每行一笔费用）
日期 / 作品·项目 / 角色 / 时段 / 句数(折合) / 费用(¥) / 甲方(棚或公司) / 是否结算 / 项目类型 / 备注
