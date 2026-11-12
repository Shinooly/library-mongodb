"""
读者管理模块
----------------
负责 readers 集合的查询、学院统计与新增读者。
"""

from datetime import datetime, timedelta, timezone

LOCAL_TZ = timezone(timedelta(hours=8))


class ReaderManager:
    """封装对 readers 集合的常用操作。"""

    def __init__(self, readers):
        self.readers = readers

    def list_all(self, limit=30):
        """列出读者。"""
        return list(self.readers.find({}, {"_id": 0}).limit(limit))

    def find_by_card(self, card_no):
        """按借阅证号查询读者。"""
        return self.readers.find_one({"card_no": card_no}, {"_id": 0})

    def count(self):
        """读者总数。"""
        return self.readers.count_documents({})

    def distinct_colleges(self):
        """全部学院名称。"""
        return self.readers.distinct("college")

    def distinct_levels(self):
        """全部读者等级。"""
        return self.readers.distinct("level")

    def college_stats(self):
        """按学院统计人数（aggregate）。"""
        pipeline = [
            {"$group": {"_id": "$college", "reader_count": {"$sum": 1}}},
            {"$sort": {"reader_count": -1}},
        ]
        return list(self.readers.aggregate(pipeline))

    def level_stats(self):
        """按等级统计人数（aggregate）。"""
        pipeline = [
            {"$group": {"_id": "$level", "reader_count": {"$sum": 1}}},
            {"$sort": {"reader_count": -1}},
        ]
        return list(self.readers.aggregate(pipeline))

    def add_reader(self, reader):
        """新增读者（insert_one），返回新文档 _id。"""
        reader.setdefault("register_date", datetime.now(LOCAL_TZ))
        return self.readers.insert_one(reader).inserted_id
