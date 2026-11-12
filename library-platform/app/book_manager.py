"""
图书管理模块
----------------
负责 books 集合的检索、评分排行与增删操作，对应任务三的六项检索。
"""

import re
from datetime import datetime, timezone, timedelta

LOCAL_TZ = timezone(timedelta(hours=8))


class BookManager:
    """封装对 books 集合的常用操作。"""

    def __init__(self, books):
        self.books = books

    # ---------------------------------- 检索 ----------------------------------
    def search_by_category_and_price(self, category, low, high, limit=50):
        """类别 + 价格区间组合筛选。"""
        cursor = self.books.find(
            {"category": category, "price": {"$gte": low, "$lte": high}},
            {"_id": 0, "title": 1, "category": 1, "price": 1, "stock": 1}
        ).sort("price", 1).limit(limit)
        return list(cursor)

    def search_by_tags(self, tags, limit=50):
        """标签多选匹配：要求同时包含全部指定标签（$all）。"""
        cursor = self.books.find(
            {"tags": {"$all": list(tags)}},
            {"_id": 0, "title": 1, "tags": 1, "category": 1}
        ).limit(limit)
        return list(cursor)

    def search_by_title(self, keyword, limit=50):
        """书名模糊检索（正则，不区分大小写）。"""
        cursor = self.books.find(
            {"title": {"$regex": re.escape(keyword), "$options": "i"}},
            {"_id": 0, "title": 1, "author": 1, "publisher": 1}
        ).limit(limit)
        return list(cursor)

    def search_by_publish_year(self, year_from, year_to, limit=50):
        """出版年份范围检索（按本地时区的年份边界换算）。"""
        start = datetime(year_from, 1, 1, tzinfo=LOCAL_TZ)
        end = datetime(year_to + 1, 1, 1, tzinfo=LOCAL_TZ)
        cursor = self.books.find(
            {"publish_date": {"$gte": start, "$lt": end}},
            {"_id": 0, "title": 1, "publish_date": 1}
        ).sort("publish_date", 1).limit(limit)
        return list(cursor)

    def missing_tags(self, limit=50):
        """数据质量核查：缺少 tags 字段的图书。"""
        cursor = self.books.find(
            {"tags": {"$exists": False}},
            {"_id": 0, "isbn": 1, "title": 1}
        ).limit(limit)
        return list(cursor)

    def top_rated(self, top_n=10):
        """评分降序取前 N 本，仅返回书名、作者、评分。"""
        cursor = self.books.find(
            {}, {"_id": 0, "title": 1, "author": 1, "rating": 1}
        ).sort("rating", -1).limit(top_n)
        return list(cursor)

    def borrow_rank(self, top_n=10):
        """借阅次数最多的图书，带出馆藏位置。"""
        cursor = self.books.find(
            {},
            {"_id": 0, "title": 1, "category": 1, "borrow_count": 1, "location": 1}
        ).sort("borrow_count", -1).limit(top_n)
        return list(cursor)

    def find_by_isbn(self, isbn):
        """按 ISBN 查询单本图书。"""
        return self.books.find_one({"isbn": isbn}, {"_id": 0})

    def count(self):
        """图书总数。"""
        return self.books.count_documents({})

    # ---------------------------------- 增删 ----------------------------------
    def add_book(self, book):
        """新增图书（insert_one），返回新文档 _id。"""
        book.setdefault("stock", 1)
        book.setdefault("borrow_count", 0)
        book.setdefault("publish_date", datetime.now(LOCAL_TZ))
        return self.books.insert_one(book).inserted_id

    def delete_by_isbn(self, isbn):
        """按 ISBN 删除图书（delete_one），返回删除条数。"""
        return self.books.delete_one({"isbn": isbn}).deleted_count
