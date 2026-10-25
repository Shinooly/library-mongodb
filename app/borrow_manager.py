"""
借阅管理模块
----------------
负责借阅登记、归还处理与逾期查询。

说明：borrow_logs 是“时间序列集合”，无 metaField 时不支持 update 操作，
      因此归还处理通过更新 books 集合的库存来完成（库存 +1）。

涉及方法：insert_one、update_one、update_many、find
"""

from datetime import datetime


class BorrowManager:
    """封装借阅流水与库存联动操作。"""

    def __init__(self, books, borrow_logs):
        self.books = books
        self.borrow_logs = borrow_logs

    # ---------------------------------- 借阅登记 ----------------------------------
    def borrow_book(self, reader_card, book_isbn):
        """
        借阅登记：向借阅流水插入一条记录（insert_one），同时扣减库存（update_one）。
        返回 (流水 _id, 库存匹配数, 库存修改数)；图书不存在时返回 (None, 0, 0)。
        """
        book = self.books.find_one({"isbn": book_isbn})
        if book is None:
            return None, 0, 0
        log = {
            "borrow_date": datetime.now(),
            "reader_card": reader_card,
            "book_isbn": book_isbn,
            "status": "借出",
        }
        log_id = self.borrow_logs.insert_one(log).inserted_id
        result = self.books.update_one(
            {"isbn": book_isbn},
            {"$inc": {"stock": -1, "borrow_count": 1}}
        )
        return log_id, result.matched_count, result.modified_count

    # ---------------------------------- 归还处理 ----------------------------------
    def return_books(self, isbn_list):
        """归还处理：按 ISBN 批量把库存加回来（update_many），返回 (匹配数, 修改数)。"""
        result = self.books.update_many(
            {"isbn": {"$in": isbn_list}},
            {"$inc": {"stock": 1}}
        )
        return result.matched_count, result.modified_count

    # ---------------------------------- 查询 ----------------------------------
    def overdue_list(self, limit=20):
        """逾期查询：状态为“逾期”的借阅记录（find）。"""
        return list(self.borrow_logs.find({"status": "逾期"}).limit(limit))

    def borrow_history(self, reader_card, limit=20):
        """某位读者的借阅历史，按借阅日期倒序（find + sort + limit）。"""
        cursor = self.borrow_logs.find({"reader_card": reader_card}).sort("borrow_date", -1)
        return list(cursor.limit(limit))

    def status_stats(self):
        """借阅流水状态统计（aggregate）。"""
        pipeline = [
            {"$group": {"_id": "$status", "数量": {"$sum": 1}}},
            {"$sort": {"数量": -1}},
        ]
        return list(self.borrow_logs.aggregate(pipeline))

    def count(self):
        """借阅流水总数。"""
        return self.borrow_logs.count_documents({})
