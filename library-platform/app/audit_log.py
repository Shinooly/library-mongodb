"""
操作日志模块
----------------
向 audit_logs 集合写入关键操作记录，并支持按时间倒序查询最近 N 条。

文档结构：
    action      操作类型（新增图书 / 删除图书 / 导出数据 / 上传文件）
    collection  涉及的集合
    target      操作对象（ISBN、文件名等）
    detail      补充说明
    operator    操作人
    created_at  操作时间
"""

import os
from datetime import datetime, timedelta, timezone

OPERATOR = os.getenv("LIB_OPERATOR", "shy")
LOCAL_TZ = timezone(timedelta(hours=8))


class AuditLogger:
    """封装 audit_logs 的写入与查询。"""

    def __init__(self, audit_logs):
        self.audit_logs = audit_logs

    def record(self, action, collection="", target="", detail=""):
        """写入一条操作日志（insert_one）。"""
        self.audit_logs.insert_one({
            "action": action,
            "collection": collection,
            "target": str(target),
            "detail": str(detail),
            "operator": OPERATOR,
            "created_at": datetime.now(LOCAL_TZ),
        })

    def recent(self, limit=100):
        """按时间倒序取最近 N 条（find + sort + limit）。"""
        cursor = self.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)
