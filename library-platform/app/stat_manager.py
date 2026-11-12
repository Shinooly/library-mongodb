"""
统计分析模块
----------------
用聚合管道实现分类统计、学院借阅排行、年月趋势与统计结果落库。
"""

import json


class StatManager:
    """封装统计类聚合查询。"""

    def __init__(self, books, borrow_logs, readers, category_stats):
        self.books = books
        self.borrow_logs = borrow_logs
        self.readers = readers
        self.category_stats_coll = category_stats

    def category_stats(self):
        """按类别统计藏书量、平均价格、平均评分与书目数。"""
        pipeline = [
            {"$group": {
                "_id": "$category",
                "total_stock": {"$sum": "$stock"},
                "avg_price": {"$avg": "$price"},
                "avg_rating": {"$avg": "$rating"},
                "book_count": {"$sum": 1},
            }},
            {"$sort": {"total_stock": -1}},
        ]
        return list(self.books.aggregate(pipeline))

    def college_borrow_top(self, top_n=5):
        """各学院借阅总量前 N 名（$lookup 关联 readers 与 borrow_logs）。"""
        pipeline = [
            {"$lookup": {"from": "borrow_logs", "localField": "card_no",
                         "foreignField": "reader_card", "as": "logs"}},
            {"$unwind": "$logs"},
            {"$group": {"_id": "$college", "borrow_total": {"$sum": 1}}},
            {"$sort": {"borrow_total": -1}},
            {"$limit": top_n},
        ]
        return list(self.readers.aggregate(pipeline))

    def borrow_trend_monthly(self):
        """按年月统计借阅量，输出“2023年01月”这样的可读标签。"""
        pipeline = [
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y年%m月", "date": "$borrow_date",
                                          "timezone": "+08:00"}},
                "borrow_total": {"$sum": 1},
            }},
            {"$sort": {"_id": 1}},
        ]
        return list(self.borrow_logs.aggregate(pipeline))

    def save_category_stats(self):
        """把分类统计结果写入 category_stats 集合（$merge）。"""
        pipeline = [
            {"$group": {
                "_id": "$category",
                "total_stock": {"$sum": "$stock"},
                "avg_price": {"$avg": "$price"},
                "avg_rating": {"$avg": "$rating"},
                "book_count": {"$sum": 1},
            }},
            {"$merge": {"into": "category_stats", "whenMatched": "replace",
                        "whenNotMatched": "insert"}},
        ]
        list(self.books.aggregate(pipeline))
        return self.category_stats_coll.count_documents({})

    def export_category_stats(self, path):
        """把 category_stats 导出为 JSON 文件，返回导出条数。

        分类名保存在 _id 中，导出时用 $project 把它改名为 category 并置于首位，
        否则导出的文件只有数字、没有类别，无法作为统计结果交付。
        """
        rows = list(self.category_stats_coll.aggregate([
            {"$sort": {"total_stock": -1}},
            {"$project": {"_id": 0, "category": "$_id", "total_stock": 1,
                          "avg_price": 1, "avg_rating": 1, "book_count": 1}},
        ]))
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(rows, fp, ensure_ascii=False, indent=2, default=str)
        return len(rows)
