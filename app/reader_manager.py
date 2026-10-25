"""
读者管理模块
----------------
负责 readers 集合的读者信息管理、学院统计与等级分布统计。

涉及方法：find、find_one、count_documents、distinct
"""

from datetime import datetime


class ReaderManager:
    """封装对 readers 集合的常用操作。"""

    def __init__(self, readers):
        self.readers = readers

    def list_all(self, limit=20):
        """列出读者（find）。"""
        return list(self.readers.find({}, {"_id": 0}).limit(limit))

    def find_by_card(self, card_no):
        """按借阅卡号查询读者（find_one），找不到返回 None。"""
        return self.readers.find_one({"card_no": card_no})

    def count(self):
        """读者总数（count_documents）。"""
        return self.readers.count_documents({})

    def distinct_colleges(self):
        """取出全部学院名称（distinct）。"""
        return self.readers.distinct("college")

    def distinct_levels(self):
        """取出全部读者等级（distinct）。"""
        return self.readers.distinct("level")

    def college_stats(self):
        """按学院统计读者人数，降序（aggregate）。"""
        pipeline = [
            {"$group": {"_id": "$college", "人数": {"$sum": 1}}},
            {"$sort": {"人数": -1}},
        ]
        return list(self.readers.aggregate(pipeline))

    def level_stats(self):
        """按等级统计读者人数，降序（aggregate）。"""
        pipeline = [
            {"$group": {"_id": "$level", "人数": {"$sum": 1}}},
            {"$sort": {"人数": -1}},
        ]
        return list(self.readers.aggregate(pipeline))

    def add_reader(self, reader):
        """新增读者（insert_one），返回新文档的 _id。"""
        reader.setdefault("fav_categories", [])
        reader.setdefault("register_date", datetime.now())
        return self.readers.insert_one(reader).inserted_id
