#!/usr/bin/env python3
"""iCloud CalDAV 配音班表管理工具

用法:
  python icloud_calendar.py list                          # 列出近期事件
  python icloud_calendar.py create "标题" 2026-07-15 10:00 11:00  # 创建事件
  python icloud_calendar.py create "标题" 2026-07-15 10:00 11:00 --desc "描述" --loc "地点"
  python icloud_calendar.py delete <uid>                  # 按 UID 删除（412 兜底强删）
  python icloud_calendar.py search "关键词"               # 按标题搜索
  python icloud_calendar.py conflict-check 2026-07-27 11:05 11:45  # 冲突检测（±7天）
  python icloud_calendar.py conflict-check 2026-07-27 11:05 11:45 --days 7  # 自定义窗口
  python icloud_calendar.py query 2026-07-25 2026-07-31   # 查询日期范围内班表
  python icloud_calendar.py delete-by-keyword "作品名"    # 按作品名批量删除（改/取消用）

依赖（需先建 venv 安装）: caldav, icalendar, tzdata(仅 Windows 需要)
  python -m venv . && Scripts/pip install caldav icalendar tzdata
"""
import sys
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from icalendar import Calendar, Event
import caldav
from icloud_config import (
    CALDAV_URL, USERNAME, PASSWORD,
    DUBBING_CALENDAR_NAME, DUBBING_CALENDAR_URL, TIMEZONE,
)

TZ = ZoneInfo(TIMEZONE)


def get_client():
    """连接 iCloud 并返回配音班表日历对象"""
    client = caldav.DAVClient(url=CALDAV_URL, username=USERNAME, password=PASSWORD)
    principal = client.principal()
    # 优先用已知 URL 直接定位
    try:
        if DUBBING_CALENDAR_URL:
            cal = caldav.objects.Calendar(client=client, url=DUBBING_CALENDAR_URL,
                                           principal=principal)
            cal.get_display_name()  # 触发验证
            return cal
    except Exception:
        pass
    # 回退：按名称查找
    for cal in principal.calendars():
        if cal.get_display_name() == DUBBING_CALENDAR_NAME:
            return cal
    # 都不行就新建
    return principal.make_calendar(name=DUBBING_CALENDAR_NAME)


def parse_dt(date_str, time_str):
    """解析 '2026-07-15' '10:00' -> timezone-aware datetime"""
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)


def create_event(summary, start_dt, end_dt, description="", location=""):
    """创建一个日历事件，返回 UID"""
    cal = get_client()
    uid = str(uuid.uuid4()) + "@dubbing-calendar"

    cal_obj = Calendar()
    cal_obj.add('prodid', '-//配音班表//iCloud CalDAV//')
    cal_obj.add('version', '2.0')

    event = Event()
    event.add('uid', uid)
    event.add('summary', summary)
    event.add('dtstart', start_dt)
    event.add('dtend', end_dt)
    event.add('dtstamp', datetime.now(TZ))
    if description:
        event.add('description', description)
    if location:
        event.add('location', location)
    cal_obj.add_component(event)

    cal.save_event(cal_obj.to_ical().decode('utf-8'))
    print(f"已创建: {summary}")
    print(f"  时间: {start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%H:%M')}")
    if location:
        print(f"  地点: {location}")
    print(f"  UID: {uid}")
    return uid


def list_events(days=30):
    """列出未来 N 天的事件"""
    cal = get_client()
    now = datetime.now(TZ)
    end = now + timedelta(days=days)
    events = cal.search(start=now, end=end, event=True, expand=True)
    if not events:
        print(f"未来 {days} 天内没有事件")
        return
    print(f"未来 {days} 天内共 {len(events)} 个事件:")
    for ev in sorted(events, key=lambda e: e.icalendar_component.get('dtstart').dt):
        comp = ev.icalendar_component
        dtstart = comp.get('dtstart').dt
        dtend = comp.get('dtend').dt
        summary = comp.get('summary', '(无标题)')
        uid = comp.get('uid')
        loc = comp.get('location', '')
        time_str = dtstart.strftime('%Y-%m-%d %H:%M') if hasattr(dtstart, 'strftime') else str(dtstart)
        end_str = dtend.strftime('%H:%M') if hasattr(dtend, 'strftime') else str(dtend)
        print(f"  {time_str}-{end_str}  {summary}" + (f"  @{loc}" if loc else ""))
        print(f"    UID: {uid}")


def delete_event(uid):
    """按 UID 删除事件（先用 search 路径拿到正确 ETag，再失败则 If-Match: * 强删）"""
    import urllib.request
    cal = get_client()
    now = datetime.now(TZ) - timedelta(days=365)
    end = now + timedelta(days=730)
    events = cal.search(start=now, end=end, event=True, expand=True)
    for ev in events:
        comp = ev.icalendar_component
        event_uid = str(comp.get('uid', ''))
        if event_uid.startswith(uid):
            try:
                ev.delete()
                print(f"已删除事件: {event_uid}")
                return
            except Exception as e:
                try:
                    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                    password_mgr.add_password(None, ev.url, USERNAME, PASSWORD)
                    auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
                    opener = urllib.request.build_opener(auth_handler)
                    req = urllib.request.Request(ev.url, method='DELETE',
                                               headers={'If-Match': '*'})
                    with opener.open(req) as resp:
                        print(f"已删除(force)事件: {event_uid}, 状态码 {resp.status}")
                    return
                except Exception as e2:
                    print(f"删除失败: {event_uid} {e2}")
                    return
    print(f"未找到 UID 匹配的事件: {uid}")


def search_events(keyword):
    """按标题关键词搜索事件"""
    cal = get_client()
    now = datetime.now(TZ) - timedelta(days=365)
    end = now + timedelta(days=730)
    events = cal.search(start=now, end=end, event=True, expand=True)
    found = []
    for ev in events:
        comp = ev.icalendar_component
        summary = str(comp.get('summary', ''))
        if keyword.lower() in summary.lower():
            found.append(ev)
    if not found:
        print(f"未找到包含 '{keyword}' 的事件")
        return
    print(f"找到 {len(found)} 个匹配事件:")
    for ev in found:
        comp = ev.icalendar_component
        dtstart = comp.get('dtstart').dt
        summary = comp.get('summary')
        uid = comp.get('uid')
        time_str = dtstart.strftime('%Y-%m-%d %H:%M') if hasattr(dtstart, 'strftime') else str(dtstart)
        print(f"  {time_str}  {summary}")
        print(f"    UID: {uid}")


def _ensure_tz(dt):
    """确保 datetime 是 timezone-aware（naive 则加 TZ）"""
    if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
        return dt.replace(tzinfo=TZ)
    return dt


def conflict_check(date_str, start_time, end_time, window_days=7):
    """检查目标时段 ±window_days 内有无时间重叠的冲突事件

    只比对 标题 + 起止时间，不拉 description 等大字段（省流量）。
    """
    cal = get_client()
    target_start = parse_dt(date_str, start_time)
    target_end = parse_dt(date_str, end_time)
    search_start = target_start - timedelta(days=window_days)
    search_end = target_end + timedelta(days=window_days)
    events = cal.search(start=search_start, end=search_end, event=True, expand=True)

    conflicts = []
    for ev in events:
        comp = ev.icalendar_component
        ev_start = _ensure_tz(comp.get('dtstart').dt)
        ev_end = _ensure_tz(comp.get('dtend').dt)
        if target_start < ev_end and target_end > ev_start:
            summary = str(comp.get('summary', '(无标题)'))
            conflicts.append((summary, ev_start, ev_end))

    if not conflicts:
        print(f"OK {date_str} {start_time}-{end_time} ±{window_days}天未检出冲突")
    else:
        print(f"CONFLICT {date_str} {start_time}-{end_time} 检出 {len(conflicts)} 个冲突:")
        for summary, ev_start, ev_end in conflicts:
            s = ev_start.strftime('%Y-%m-%d %H:%M') if hasattr(ev_start, 'strftime') else str(ev_start)
            e = ev_end.strftime('%H:%M') if hasattr(ev_end, 'strftime') else str(ev_end)
            print(f"  ⚠ {s}-{e}  {summary}")


def query_events(start_date, end_date):
    """查询指定日期范围内的班表事件，精简输出（标题+时间+地点）"""
    cal = get_client()
    start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=TZ)
    end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=TZ) + timedelta(days=1)
    events = cal.search(start=start, end=end, event=True, expand=True)
    if not events:
        print(f"{start_date} ~ {end_date} 没有班表事件")
        return
    print(f"{start_date} ~ {end_date} 共 {len(events)} 场:")
    for ev in sorted(events, key=lambda e: e.icalendar_component.get('dtstart').dt):
        comp = ev.icalendar_component
        dtstart = _ensure_tz(comp.get('dtstart').dt)
        dtend = _ensure_tz(comp.get('dtend').dt)
        summary = str(comp.get('summary', '(无标题)'))
        loc = str(comp.get('location', ''))
        time_str = dtstart.strftime('%m/%d %H:%M') if hasattr(dtstart, 'strftime') else str(dtstart)
        end_str = dtend.strftime('%H:%M') if hasattr(dtend, 'strftime') else str(dtend)
        line = f"  {time_str}-{end_str}  {summary}"
        if loc:
            line += f"  @{loc}"
        print(line)


def delete_by_keyword(keyword):
    """按标题关键词删除所有匹配事件（改/取消口语指令用，内部 search->delete）

    复用 delete_event 的 412 兜底逻辑。
    """
    import urllib.request
    cal = get_client()
    now = datetime.now(TZ) - timedelta(days=365)
    end = now + timedelta(days=730)
    events = cal.search(start=now, end=end, event=True, expand=True)
    deleted = 0
    for ev in events:
        comp = ev.icalendar_component
        summary = str(comp.get('summary', ''))
        if keyword.lower() in summary.lower():
            uid = str(comp.get('uid', ''))
            try:
                ev.delete()
                print(f"已删除: {summary}  UID: {uid}")
                deleted += 1
            except Exception:
                try:
                    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                    password_mgr.add_password(None, ev.url, USERNAME, PASSWORD)
                    auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
                    opener = urllib.request.build_opener(auth_handler)
                    req = urllib.request.Request(ev.url, method='DELETE',
                                                headers={'If-Match': '*'})
                    with opener.open(req) as resp:
                        pass
                    print(f"已删除(force): {summary}  UID: {uid}")
                    deleted += 1
                except Exception as e2:
                    print(f"删除失败: {summary}  UID: {uid}  {e2}")
    if deleted == 0:
        print(f"未找到包含 '{keyword}' 的事件")
    else:
        print(f"共删除 {deleted} 个事件")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'list':
        list_events()

    elif cmd == 'create':
        if len(sys.argv) < 5:
            print("用法: create \"标题\" 2026-07-15 10:00 11:00 [--desc \"描述\"] [--loc \"地点\"]")
            sys.exit(1)
        summary = sys.argv[2]
        date_str = sys.argv[3]
        start_time = sys.argv[4]
        end_time = sys.argv[5] if len(sys.argv) > 5 else None
        desc = ""
        loc = ""
        i = 6
        while i < len(sys.argv):
            if sys.argv[i] == '--desc' and i + 1 < len(sys.argv):
                desc = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--loc' and i + 1 < len(sys.argv):
                loc = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        start_dt = parse_dt(date_str, start_time)
        if end_time:
            end_dt = parse_dt(date_str, end_time)
        else:
            end_dt = start_dt.replace(hour=start_dt.hour + 1)
        create_event(summary, start_dt, end_dt, desc, loc)

    elif cmd == 'delete':
        if len(sys.argv) < 3:
            print("用法: delete <uid>")
            sys.exit(1)
        delete_event(sys.argv[2])

    elif cmd == 'search':
        if len(sys.argv) < 3:
            print("用法: search \"关键词\"")
            sys.exit(1)
        search_events(sys.argv[2])

    elif cmd == 'conflict-check':
        if len(sys.argv) < 5:
            print("用法: conflict-check 2026-07-27 11:05 11:45 [--days 7]")
            sys.exit(1)
        date_str = sys.argv[2]
        start_time = sys.argv[3]
        end_time = sys.argv[4]
        window = 7
        if '--days' in sys.argv:
            idx = sys.argv.index('--days')
            if idx + 1 < len(sys.argv):
                window = int(sys.argv[idx + 1])
        conflict_check(date_str, start_time, end_time, window)

    elif cmd == 'query':
        if len(sys.argv) < 4:
            print("用法: query 2026-07-25 2026-07-31")
            sys.exit(1)
        query_events(sys.argv[2], sys.argv[3])

    elif cmd == 'delete-by-keyword':
        if len(sys.argv) < 3:
            print("用法: delete-by-keyword \"作品名\"")
            sys.exit(1)
        delete_by_keyword(sys.argv[2])

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
