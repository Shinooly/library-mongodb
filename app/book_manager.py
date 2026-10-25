"""
图书管理模块
----------------
负责 books 集合的增删改查、条件检索与评分排行。

涉及方法：insert_one、insert_many、find、find_one、update_one、update_many、
          delete_one、delete_many
"""

from datetime import datetime


class BookManager:
    """封装对 books 集合的常用操作。"""

    def __init__(self, books):
        self.books = books

    # ---------------------------------- 检索 ----------------------------------
    def search_by_category(self, category, limit=20):
        """按类别检索图书（find）。"""
        return list(self.books.find({"category": category}).limit(limit))

    def search_by_price_range(self, low, high, limit=20):
        """按价格区间检索图书，价格升序（find）。"""
        cursor = self.books.find({"price": {"$gte": low, "$lte": high}}).sort("price", 1).limit(limit)
        return list(cursor)

    def find_by_isbn(self, isbn):
        """按 ISBN 精确查询单本图书（find_one），找不到返回 None。"""
        return self.books.find_one({"isbn": isbn})

    def rating_rank(self, top_n=5):
        """按评分降序取前 N 本图书（find + sort + limit）。"""
        cursor = self.books.find({}, {"_id": 0, "title": 1, "rating": 1, "borrow_count": 1})
        return list(cursor.sort("rating", -1).limit(top_n))

    def count(self):
        """图书总数。"""
        return self.books.count_documents({})

    # ---------------------------------- 新增 ----------------------------------
    def add_book(self, book):
        """新增一本图书（insert_one），返回新文档的 _id。"""
        book.setdefault("tags", [])
        book.setdefault("stock", 1)
        book.setdefault("borrow_count", 0)
        book.setdefault("last-updated", datetime.now())
        result = self.books.insert_one(book)
        return result.inserted_id

    def add_books(self, book_list):
        """批量新增图书（insert_many），返回插入条数。"""
        if not book_list:
            return 0
        for book in book_list:
            book.setdefault("tags", [])
            book.setdefault("borrow_count", 0)
            book.setdefault("last-updated", datetime.now())
        result = self.books.insert_many(book_list)
        return len(result.inserted_ids)

    # ---------------------------------- 更新 ----------------------------------
    def update_stock(self, isbn, delta):
        """调整某本书的库存（update_one + $inc），返回 (匹配数, 修改数)。"""
        result = self.books.update_one(
            {"isbn": isbn},
            {"$inc": {"stock": delta}, "$currentDate": {"last-updated": True}}
        )
        return result.matched_count, result.modified_count

    def update_price_by_category(self, category, ratio):
        """按类别批量调整价格（update_many + $mul），返回 (匹配数, 修改数)。"""
        result = self.books.update_many(
            {"category": category},
            {"$mul": {"price": ratio}, "$currentDate": {"last-updated": True}}
        )
        return result.matched_count, result.modified_count

    # ---------------------------------- 删除 ----------------------------------
    def delete_by_isbn(self, isbn):
        """按 ISBN 删除一本图书（delete_one），返回删除条数。"""
        result = self.books.delete_one({"isbn": isbn})
        return result.deleted_count

    def delete_by_category(self, category):
        """按类别批量删除图书（delete_many），返回删除条数。"""
        result = self.books.delete_many({"category": category})
        return result.deleted_count
