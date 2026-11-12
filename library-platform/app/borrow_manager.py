"""
借阅管理模块
----------------
负责借阅登记、归还处理与逾期查询。

说明：borrow_logs 是时间序列集合（timeField=borrow_date），
      没有 metaField 时不支持修改已有文档，因此归还处理只更新 books 的库存。
"""

from datetime import datetime, timedelta, timezone

LOCAL_TZ = timezone(timedelta(hours=8))


class BorrowManager:
    """封装借阅流水与库存联动操作。"""

    def __init__(self, books, borrow_logs):
        self.books = books
        self.borrow_logs = borrow_logs

    def borrow_book(self, reader_card, book_isbn):
        """
        借阅登记：插入一条流水并扣减库存。
        返回 (流水 _id, 库存匹配数, 库存修改数)；图书不存在时返回 (None, 0, 0)。
        """
        book = self.books.find_one({"isbn": book_isbn}, {"title": 1})
        if book is None:
            return None, 0, 0
        log = {
            "borrow_date": datetime.now(LOCAL_TZ),
            "reader_card": reader_card,
            "book_isbn": book_isbn,
            "status": "借出",
            "duration_days": 0,
        }
        log_id = self.borrow_logs.insert_one(log).inserted_id
        result = self.books.update_one(
            {"isbn": book_isbn},
            {"$inc": {"stock": -1, "borrow_count": 1}}
        )
        return log_id, result.matched_count, result.modified_count

    def return_books(self, isbn_list):
        """归还处理：按 ISBN 批量把库存加回来。"""
        result = self.books.update_many({"isbn": {"$in": isbn_list}}, {"$inc": {"stock": 1}})
        return result.matched_count, result.modified_count

    def overdue_list(self, limit=20):
        """逾期记录。"""
        cursor = self.borrow_logs.find(
            {"status": "逾期"},
            {"_id": 0, "reader_card": 1, "book_isbn": 1, "borrow_date": 1, "duration_days": 1}
        ).limit(limit)
        return list(cursor)

    def borrow_history(self, reader_card, limit=20):
        """某位读者的借阅历史，按借阅时间倒序。"""
        cursor = self.borrow_logs.find(
            {"reader_card": reader_card},
            {"_id": 0, "book_isbn": 1, "borrow_date": 1, "status": 1}
        ).sort("borrow_date", -1).limit(limit)
        return list(cursor)

    def status_stats(self):
        """按状态统计流水数量。"""
        pipeline = [
            {"$group": {"_id": "$status", "log_count": {"$sum": 1}}},
            {"$sort": {"log_count": -1}},
        ]
        return list(self.borrow_logs.aggregate(pipeline))

    def count(self):
        """流水总数。"""
        return self.borrow_logs.count_documents({})
