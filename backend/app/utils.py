"""
共享工具函数模块。

提取 routes.py 和 admin_routes.py 中重复使用的辅助函数，
避免代码重复，提高可维护性。
"""

from datetime import datetime, timezone


def safe_isoformat(value, default=None):
    """安全将日期转为 ISO 字符串，兼容 datetime 对象和无效日期字符串（如 '0000-00-00'）。

    用于 API 响应中统一日期时间格式，替代 routes.py 和 admin_routes.py 中的重复定义。
    """
    if value is None:
        return default
    if isinstance(value, datetime):
        return value.isoformat()
    s = str(value)
    if s.startswith('0000') or s.startswith('00'):
        return default
    return s[:19] if len(s) >= 10 else s


def parse_genres(genres_str):
    """将管道分隔的 genre 字符串解析为 genre 列表。

    过滤掉 "(no genres listed)" 等无效值，
    返回清理后的 genre 名称列表。
    """
    if not genres_str:
        return []
    return [
        g.strip()
        for g in str(genres_str).split("|")
        if g.strip() and g.strip() != "(no genres listed)"
    ]


def utcnow():
    """返回 naive UTC datetime，兼容 SQLite（不支持时区感知 datetime）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)
