"""
统计分析模块
----------------
用聚合管道（aggregate）实现分类统计、借阅趋势与畅销榜。
"""


class StatManager:
    """封装统计类聚合查询。"""

    def __init__(self, books, borrow_logs):
        self.books = books
        self.borrow_logs = borrow_logs

    def category_stats(self):
        """
        分类统计：按类别分组，统计库存总量、平均价格、图书数量，
        并按库存总量降序排列。
        """
        pipeline = [
            {"$group": {
                "_id": "$category",
                "库存总量": {"$sum": "$stock"},
                "平均价格": {"$avg": "$price"},
                "图书数量": {"$sum": 1},
            }},
            {"$sort": {"库存总量": -1}},
        ]
        return list(self.books.aggregate(pipeline))

    def borrow_trend(self):
        """借阅趋势：按年份分组统计借阅量，格式化为“2024年”这样的字符串。"""
        pipeline = [
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y年", "date": "$borrow_date"}},
                "借阅量": {"$sum": 1},
            }},
            {"$sort": {"_id": 1}},
        ]
        return list(self.borrow_logs.aggregate(pipeline))

    def best_sellers(self, top_n=5):
        """畅销榜：按借阅次数降序取前 N 本图书。"""
        pipeline = [
            {"$sort": {"borrow_count": -1}},
            {"$limit": top_n},
            {"$project": {"_id": 0, "title": 1, "category": 1, "borrow_count": 1}},
        ]
        return list(self.books.aggregate(pipeline))
