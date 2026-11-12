"""
数据清洗与导入脚本
--------------------
把学生包里的三份 JSON 数据读入 MongoDB，并在导入过程中完成类型转换：

  * ISO 8601 日期字符串  ->  Date 类型
  * 价格 / 评分          ->  Double
  * 库存 / 借阅次数 / 时长 / 复本数 -> Int
  * location 保持嵌套文档，缺 tags / fav_categories 的文档保持缺失

用法：
    python scripts/data_clean.py
    python scripts/data_clean.py --data-dir ../03-数据 --uri "mongodb://user:pwd@127.0.0.1:27017/library?authSource=library"

导入完成后会打印三个集合的文档数，便于和源文件条目数（50 / 30 / 3000）核对。
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

from pymongo import MongoClient
from pymongo.errors import PyMongoError

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DEFAULT_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/library_platform")
DB_NAME = os.getenv("MONGO_DB", "library_platform")
LOCAL_TZ = timezone(timedelta(hours=8))


def load_json(path):
    """读取 JSON 数组或对象。"""
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def parse_date(value):
    """把 ISO 8601 字符串转成带时区的 datetime；空值保持为空。"""
    if value is None:
        return None
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def clean_book(raw):
    """清洗一条图书数据。"""
    doc = {}
    for field in ("isbn", "title", "author", "publisher", "category"):
        doc[field] = raw.get(field)

    doc["price"] = float(raw["price"]) if raw.get("price") is not None else None
    doc["rating"] = float(raw["rating"]) if raw.get("rating") is not None else None
    doc["stock"] = int(raw["stock"]) if raw.get("stock") is not None else None
    doc["borrow_count"] = int(raw["borrow_count"]) if raw.get("borrow_count") is not None else None
    doc["publish_date"] = parse_date(raw.get("publish_date"))

    if "location" in raw and raw["location"] is not None:
        loc = raw["location"]
        doc["location"] = {
            "floor": loc.get("floor"),
            "shelf": loc.get("shelf"),
            "copies": int(loc["copies"]) if loc.get("copies") is not None else None,
        }
    # tags 与 ebook_name 是“部分图书才有”的字段，缺失时不补默认值
    if "tags" in raw and raw["tags"] is not None:
        doc["tags"] = list(raw["tags"])
    if "ebook_name" in raw and raw["ebook_name"] is not None:
        doc["ebook_name"] = raw["ebook_name"]
    return doc


def clean_reader(raw):
    """清洗一条读者数据。"""
    doc = {}
    for field in ("card_no", "name", "college", "phone", "level"):
        doc[field] = raw.get(field)
    doc["email"] = raw.get("email")  # 允许为 null
    doc["register_date"] = parse_date(raw.get("register_date"))
    if "fav_categories" in raw and raw["fav_categories"] is not None:
        doc["fav_categories"] = list(raw["fav_categories"])
    return doc


def clean_borrow_log(raw):
    """清洗一条借阅流水。"""
    doc = {
        "borrow_date": parse_date(raw.get("borrow_date")),
        "reader_card": raw.get("reader_card"),
        "book_isbn": raw.get("book_isbn"),
        "status": raw.get("status"),
        "duration_days": int(raw["duration_days"]) if raw.get("duration_days") is not None else None,
    }
    if raw.get("return_date") is not None:
        doc["return_date"] = parse_date(raw["return_date"])
    return doc


def rebuild_collections(db):
    """重建本次项目用到的集合（重复执行时不会叠加旧数据）。"""
    for name in ("books", "readers", "borrow_logs", "audit_logs", "category_stats"):
        db.drop_collection(name)

    db.create_collection("books")
    db.create_collection("readers")
    # 借阅流水按时序增长，使用时间序列集合；不设置 expireAfterSeconds，避免历史数据被自动清理
    db.create_collection("borrow_logs", timeseries={"timeField": "borrow_date", "metaField": "reader_card", "granularity": "hours"})
    db.create_collection("audit_logs")
    db.create_collection("category_stats")
    db.audit_logs.create_index([("created_at", -1)], name="idx_audit_time")


def main():
    parser = argparse.ArgumentParser(description="清洗并导入智慧图书馆数据")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="数据目录（含 books.txt / readers.txt / borrow_logs.txt）")
    parser.add_argument("--uri", default=DEFAULT_URI, help="MongoDB 连接串")
    parser.add_argument("--db", default=DB_NAME, help="数据库名")
    args = parser.parse_args()

    book_path = os.path.join(args.data_dir, "books.txt")
    reader_path = os.path.join(args.data_dir, "readers.txt")
    log_path = os.path.join(args.data_dir, "borrow_logs.txt")
    for path in (book_path, reader_path, log_path):
        if not os.path.exists(path):
            print("找不到数据文件：%s" % path)
            sys.exit(1)

    books = [clean_book(item) for item in load_json(book_path)]
    readers = [clean_reader(item) for item in load_json(reader_path)]
    logs = [clean_borrow_log(item) for item in load_json(log_path)]

    print("源文件条目数：books=%d  readers=%d  borrow_logs=%d" % (len(books), len(readers), len(logs)))

    client = MongoClient(args.uri, serverSelectionTimeoutMS=5000, tz_aware=True, tzinfo=LOCAL_TZ)
    try:
        client.admin.command("ping")
        db = client[args.db]
        rebuild_collections(db)

        if books:
            db.books.insert_many(books)
        if readers:
            db.readers.insert_many(readers)
        # 3000 条流水一次插入，失败时便于整批排查
        if logs:
            db.borrow_logs.insert_many(logs)

        print("\n导入后文档数：")
        print("  books        = %d" % db.books.count_documents({}))
        print("  readers      = %d" % db.readers.count_documents({}))
        print("  borrow_logs  = %d" % db.borrow_logs.count_documents({}))

        print("\n字段抽样（确认类型已转换）：")
        sample = db.books.find_one({"isbn": "9787115428028"}, {"_id": 0})
        if sample:
            print("  publish_date 类型：%s，值：%s" % (type(sample.get("publish_date")).__name__, sample.get("publish_date")))
            print("  price 类型：%s，值：%s" % (type(sample.get("price")).__name__, sample.get("price")))
            print("  stock 类型：%s，值：%s" % (type(sample.get("stock")).__name__, sample.get("stock")))

        ok = (
            db.books.count_documents({}) == len(books)
            and db.readers.count_documents({}) == len(readers)
            and db.borrow_logs.count_documents({}) == len(logs)
        )
        print("\n核对结果：%s" % ("三个集合数量与源文件一致" if ok else "数量不一致，请检查"))
    except PyMongoError as exc:
        print("导入失败：%s" % exc)
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
