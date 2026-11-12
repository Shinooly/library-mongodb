"""
主程序
----------------
智慧图书馆数字资源平台的菜单式入口，串联图书检索、统计分析、
GridFS 文件存储与操作日志。

运行方式：
    cd app
    python main.py

数据目录默认为项目下的 data/，可用环境变量 LIB_DATA_DIR 覆盖。
"""

import os
import sys
from datetime import datetime

import mongodb_connect as dbc
from audit_log import AuditLogger
from book_manager import BookManager
from borrow_manager import BorrowManager
from gridfs_manager import GridfsManager
from reader_manager import ReaderManager
from stat_manager import StatManager

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.getenv("LIB_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
EXPORT_DIR = os.path.join(PROJECT_ROOT, "exports")

CATEGORIES = ["计算机", "文学", "经济管理", "数学", "外语", "历史"]

MENU = """
=============== 智慧图书馆数字资源平台 ===============
   1. 类别 + 价格区间检索         2. 标签多选检索
   3. 书名模糊检索                4. 出版年份范围检索
   5. 缺少 tags 数据核查          6. 评分 Top 10
   7. 分类统计（藏书量/均价/评分）  8. 学院借阅 Top 5
   9. 年月借阅趋势               10. 借阅 Top 10 + 馆藏位置
  11. 分类统计写入集合           12. 导出分类统计
  13. 上传电子书与封面（GridFS）  14. 按书名下载电子书并校验
  15. GridFS 文件清单            16. 新增图书
  17. 删除图书                   18. 最近 100 条操作日志
   0. 退出
======================================================
"""


# ============================== 输出辅助 ==============================
def fmt_num(value, pattern):
    """格式化数值，避免浮点残留。"""
    return pattern % value if isinstance(value, (int, float)) else "-"


def fmt_time(value, pattern="%Y-%m-%d"):
    """格式化日期。"""
    if isinstance(value, datetime):
        return value.strftime(pattern)
    return "-"


def choose_category():
    """按编号或名称选择类别。"""
    print("可选类别：" + " / ".join("%d.%s" % (i, n) for i, n in enumerate(CATEGORIES, start=1)))
    raw = input("请输入类别编号或名称：").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(CATEGORIES):
        return CATEGORIES[int(raw) - 1]
    return raw


def show_book_titles(rows, empty_hint):
    """统一打印检索结果。"""
    if not rows:
        print("提示：" + empty_hint)
        return
    print("查询到 %d 条记录：" % len(rows))
    for row in rows:
        print("  " + str(row.get("title", "")))


# ============================== 检索功能 ==============================
def do_search_category_price(book_mgr):
    category = choose_category()
    try:
        low = float(input("最低价：").strip())
        high = float(input("最高价：").strip())
    except ValueError:
        print("提示：价格必须是数字。")
        return
    rows = book_mgr.search_by_category_and_price(category, low, high)
    if not rows:
        print("提示：没有「%s」且价格在 %s ~ %s 元之间的图书。" % (category, low, high))
        return
    print("查询到 %d 条记录：" % len(rows))
    for row in rows:
        print("  %-28s %8s 元  库存 %s" % (str(row.get("title", ""))[:26],
                                          fmt_num(row.get("price"), "%.2f"),
                                          fmt_num(row.get("stock"), "%d")))


def do_search_tags(book_mgr):
    raw = input("请输入标签，多个用英文逗号分隔（如 编程,Python）：").strip()
    tags = [t.strip() for t in raw.replace("，", ",").split(",") if t.strip()]
    if not tags:
        print("提示：至少输入一个标签。")
        return
    rows = book_mgr.search_by_tags(tags)
    if not rows:
        print("提示：没有同时包含这些标签的图书。")
        return
    print("查询到 %d 条记录：" % len(rows))
    for row in rows:
        print("  %-28s %s" % (str(row.get("title", ""))[:26], "、".join(row.get("tags", []))))


def do_search_title(book_mgr):
    keyword = input("请输入书名关键字：").strip()
    if not keyword:
        print("提示：关键字不能为空。")
        return
    show_book_titles(book_mgr.search_by_title(keyword), "没有书名包含「%s」的图书。" % keyword)


def do_search_publish_year(book_mgr):
    try:
        year_from = int(input("起始年份（如 2023）：").strip())
        year_to = int(input("结束年份（如 2024）：").strip())
    except ValueError:
        print("提示：年份必须是数字。")
        return
    rows = book_mgr.search_by_publish_year(year_from, year_to)
    if not rows:
        print("提示：没有出版日期在 %d—%d 年的图书。" % (year_from, year_to))
        return
    print("查询到 %d 条记录：" % len(rows))
    for row in rows:
        print("  %-28s %s" % (str(row.get("title", ""))[:26], fmt_time(row.get("publish_date"))))


def do_missing_tags(book_mgr):
    rows = book_mgr.missing_tags()
    if not rows:
        print("提示：所有图书都有 tags 字段。")
        return
    print("缺少 tags 字段的图书共 %d 本：" % len(rows))
    for row in rows:
        print("  %s  %s" % (row.get("isbn", "-"), row.get("title", "")))


def do_top_rated(book_mgr):
    rows = book_mgr.top_rated(10)
    print("评分 Top 10：")
    for i, row in enumerate(rows, start=1):
        print("  第%2d名  %-28s %-12s 评分 %s" % (
            i, str(row.get("title", ""))[:26], str(row.get("author", ""))[:10],
            fmt_num(row.get("rating"), "%.1f")))


# ============================== 统计功能 ==============================
def do_category_stats(stat_mgr):
    rows = stat_mgr.category_stats()
    if not rows:
        print("提示：没有统计数据。")
        return
    print("  %-8s %8s %10s %10s %8s" % ("类别", "书目数", "藏书量", "平均价格", "平均评分"))
    for row in rows:
        print("  %-8s %8d %10d %10s %8s" % (
            row["_id"], row["book_count"], row["total_stock"],
            fmt_num(row.get("avg_price"), "%.2f"), fmt_num(row.get("avg_rating"), "%.2f")))


def do_college_borrow(stat_mgr):
    rows = stat_mgr.college_borrow_top(5)
    if not rows:
        print("提示：没有借阅记录。")
        return
    print("学院借阅总量 Top 5：")
    for i, row in enumerate(rows, start=1):
        print("  第%d名  %-14s %d 次" % (i, row["_id"], row["borrow_total"]))


def do_borrow_trend(stat_mgr):
    rows = stat_mgr.borrow_trend_monthly()
    if not rows:
        print("提示：没有借阅记录。")
        return
    print("年月借阅趋势（共 %d 个月）：" % len(rows))
    for row in rows:
        print("  %s ： %d 次" % (row["_id"], row["borrow_total"]))


def do_borrow_rank(book_mgr):
    rows = book_mgr.borrow_rank(10)
    print("借阅次数 Top 10：")
    for i, row in enumerate(rows, start=1):
        loc = row.get("location") or {}
        print("  第%2d名  %-26s %6s 次  %s / %s / 复本 %s" % (
            i, str(row.get("title", ""))[:24], fmt_num(row.get("borrow_count"), "%d"),
            loc.get("floor", "-"), loc.get("shelf", "-"), loc.get("copies", "-")))


def do_save_stats(stat_mgr):
    count = stat_mgr.save_category_stats()
    print("分类统计已写入 category_stats，当前共 %d 条记录。" % count)


def do_export_stats(stat_mgr, audit):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, "category_stats.json")
    count = stat_mgr.export_category_stats(path)
    audit.record("导出数据", "category_stats", path, "导出 %d 条分类统计" % count)
    print("导出完成：%d 条，文件 %s" % (count, path))


# ============================== GridFS ==============================
def do_upload_files(gridfs_mgr, audit):
    manifest = os.path.join(DATA_DIR, "gridfs_files", "files_manifest.txt")
    files_dir = os.path.join(DATA_DIR, "gridfs_files")
    if not os.path.isfile(manifest):
        print("找不到文件清单：%s" % manifest)
        return
    report = gridfs_mgr.upload_manifest(manifest, files_dir)
    print("上传结果：")
    for name, message in report:
        print("  %-14s %s" % (name, message))
    uploaded = len([1 for _, msg in report if "上传成功" in msg])
    audit.record("上传文件", "fs.files", "批量上传", "新增 %d 个文件" % uploaded)


def do_download_ebook(gridfs_mgr):
    title = input("请输入书名（支持部分匹配）：").strip()
    if not title:
        print("提示：书名不能为空。")
        return
    result = gridfs_mgr.download_by_title(title, EXPORT_DIR)
    if result["status"] == "no_book":
        print("提示：没有找到书名包含「%s」的图书。" % title)
        return
    if result["status"] == "no_ebook":
        print("图书「%s」没有关联电子书。" % result["book"]["title"])
        return
    print("图书：%s（ISBN %s）" % (result["book"]["title"], result["book"]["isbn"]))
    print("下载文件：%s" % result["path"])
    print("上传时字节数：%d" % result["stored_bytes"])
    print("下载后字节数：%d" % result["downloaded_bytes"])
    print("校验结果：%s" % ("一致" if result["match"] else "不一致"))


def do_list_files(gridfs_mgr):
    rows = gridfs_mgr.list_files()
    if not rows:
        print("提示：GridFS 中还没有文件。")
        return
    print("GridFS 文件共 %d 个：" % len(rows))
    print("  %-14s %8s  %-19s  %-6s %s" % ("文件名", "字节", "上传时间", "类型", "关联 ISBN"))
    for row in rows:
        print("  %-14s %8d  %-19s  %-6s %s" % (
            row["filename"], row["length"],
            fmt_time(row["upload_date"], "%Y-%m-%d %H:%M:%S"),
            row["file_type"], row["related_isbn"]))


# ============================== 图书增删 ==============================
def do_add_book(book_mgr, audit):
    isbn = input("ISBN（13 位）：").strip()
    if book_mgr.find_by_isbn(isbn) is not None:
        print("提示：ISBN 已存在，不能重复新增。")
        return
    title = input("书名：").strip()
    author = input("作者：").strip()
    publisher = input("出版社：").strip()
    category = choose_category()
    try:
        price = float(input("单价：").strip())
        stock = int(input("库存：").strip())
        rating = float(input("评分：").strip())
    except ValueError:
        print("提示：价格 / 库存 / 评分必须是数字，本次新增已取消。")
        return
    new_id = book_mgr.add_book({
        "isbn": isbn, "title": title, "author": author, "publisher": publisher,
        "category": category, "price": price, "stock": stock, "rating": rating,
        "borrow_count": 0, "tags": [category],
    })
    audit.record("新增图书", "books", isbn, title)
    print("新增成功，_id = %s" % new_id)


def do_delete_book(book_mgr, audit):
    isbn = input("请输入要删除的 ISBN：").strip()
    deleted = book_mgr.delete_by_isbn(isbn)
    if deleted == 0:
        print("提示：没有找到 ISBN 为 %s 的图书。" % isbn)
        return
    audit.record("删除图书", "books", isbn, "删除 %d 条" % deleted)
    print("删除完成，实际删除 %d 条文档。" % deleted)


def do_recent_logs(audit):
    rows = audit.recent(100)
    if not rows:
        print("提示：还没有操作日志。")
        return
    print("最近 %d 条操作日志（按时间倒序）：" % len(rows))
    for row in rows[:20]:
        print("  %s  %-8s %-10s %s" % (
            fmt_time(row.get("created_at"), "%Y-%m-%d %H:%M:%S"),
            row.get("action", "-"), row.get("target", "-"), row.get("detail", "")))
    if len(rows) > 20:
        print("  …… 其余 %d 条已省略" % (len(rows) - 20))


# ============================== 启动与主循环 ==============================
def print_startup_info(book_mgr, reader_mgr, borrow_mgr, audit):
    print("=" * 62)
    print("数据库连接状态：连接成功")
    print("  连接串：%s" % dbc.MONGO_URI)
    print("  当前库：%s" % dbc.DB_NAME)
    print("集合文档数：books=%d, readers=%d, borrow_logs=%d, audit_logs=%d, category_stats=%d" % (
        book_mgr.count(), reader_mgr.count(), borrow_mgr.count(),
        audit.audit_logs.count_documents({}), dbc.get_collection("category_stats").count_documents({}),
    ))
    print("GridFS 文件数：%d" % dbc.get_db()["fs.files"].count_documents({}))
    print("=" * 62)


def main():
    if not dbc.test_connection():
        print("无法连接数据库，请检查 MongoDB 服务与 MONGO_URI 配置。")
        sys.exit(1)

    db = dbc.get_db()
    book_mgr = BookManager(dbc.get_collection("books"))
    reader_mgr = ReaderManager(dbc.get_collection("readers"))
    borrow_mgr = BorrowManager(dbc.get_collection("books"), dbc.get_collection("borrow_logs"))
    stat_mgr = StatManager(dbc.get_collection("books"), dbc.get_collection("borrow_logs"),
                           dbc.get_collection("readers"), dbc.get_collection("category_stats"))
    gridfs_mgr = GridfsManager(db, dbc.get_collection("books"))
    audit = AuditLogger(dbc.get_collection("audit_logs"))

    print_startup_info(book_mgr, reader_mgr, borrow_mgr, audit)

    actions = {
        "1": lambda: do_search_category_price(book_mgr),
        "2": lambda: do_search_tags(book_mgr),
        "3": lambda: do_search_title(book_mgr),
        "4": lambda: do_search_publish_year(book_mgr),
        "5": lambda: do_missing_tags(book_mgr),
        "6": lambda: do_top_rated(book_mgr),
        "7": lambda: do_category_stats(stat_mgr),
        "8": lambda: do_college_borrow(stat_mgr),
        "9": lambda: do_borrow_trend(stat_mgr),
        "10": lambda: do_borrow_rank(book_mgr),
        "11": lambda: do_save_stats(stat_mgr),
        "12": lambda: do_export_stats(stat_mgr, audit),
        "13": lambda: do_upload_files(gridfs_mgr, audit),
        "14": lambda: do_download_ebook(gridfs_mgr),
        "15": lambda: do_list_files(gridfs_mgr),
        "16": lambda: do_add_book(book_mgr, audit),
        "17": lambda: do_delete_book(book_mgr, audit),
        "18": lambda: do_recent_logs(audit),
    }

    while True:
        print(MENU)
        choice = input("请选择功能编号：").strip()
        if choice == "0":
            break
        handler = actions.get(choice)
        if handler is None:
            print("提示：无效的编号，请重新选择。")
            continue
        try:
            handler()
        except Exception as exc:
            print("操作出错：%s" % exc)
        print()

    dbc.close()
    print("数据库连接已关闭，程序退出。")


if __name__ == "__main__":
    main()
