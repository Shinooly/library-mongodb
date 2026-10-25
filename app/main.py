"""
主程序
----------------
图书情报检索与统计平台的菜单式交互入口，串联各功能模块。

作者：__________    日期：__________
运行方式：在 PyCharm 中直接运行本文件，或在项目目录下执行  python3 main.py
"""

import sys
import time
from datetime import datetime

import mongodb_connect as dbc
from book_manager import BookManager
from reader_manager import ReaderManager
from borrow_manager import BorrowManager
from stat_manager import StatManager

MENU = """
================== 图书情报检索与统计平台 ==================
   1. 按类别检索图书              2. 按价格区间检索图书
   3. 按 ISBN 查询单本图书        4. 新增图书
   5. 批量新增图书                6. 更新图书库存
   7. 按类别批量调价              8. 删除图书（按 ISBN）
   9. 批量删除某类别图书         10. 分类统计（库存/均价/数量）
  11. 借阅趋势统计（按年份）     12. 畅销榜 Top N
  13. 读者信息管理               14. 借阅登记
  15. 归还处理                   16. 逾期查询
   0. 退出
============================================================
"""


# ============================== 公共输出函数 ==============================
def _num(value, pattern):
    """把数值格式化成字符串，避免出现 80.10000000000001 这类浮点残留。"""
    return pattern % value if isinstance(value, (int, float)) else "-"


def show_books(books, empty_hint="没有查询到符合条件的图书。"):
    """打印图书列表；为空时给出明确提示。"""
    if not books:
        print("提示：" + empty_hint)
        return
    print("查询到 %d 条记录：" % len(books))
    print("  %-30s %-8s %8s %6s %6s %6s" % ("书名", "类别", "价格", "评分", "库存", "借阅"))
    for book in books:
        print("  %-30s %-8s %8s %6s %6s %6s" % (
            str(book.get("title", ""))[:28],
            str(book.get("category", "-")),
            _num(book.get("price"), "%.2f"),
            _num(book.get("rating"), "%.1f"),
            _num(book.get("stock"), "%d"),
            _num(book.get("borrow_count"), "%d"),
        ))


def print_startup_info(book_mgr, reader_mgr, borrow_mgr):
    """启动时打印数据库连接状态与各集合文档总数。"""
    print("=" * 60)
    print("数据库连接状态：" + ("连接成功" if dbc.test_connection() else "连接失败"))
    print("  当前库：%s    连接账号：%s" % (dbc.DB_NAME, dbc.MONGO_USER))
    print("集合文档总数：books=%d, readers=%d, borrow_logs=%d, book_logs=%d, category_stats=%d" % (
        book_mgr.count(), reader_mgr.count(), borrow_mgr.count(),
        dbc.get_collection("book_logs").count_documents({}),
        dbc.get_collection("category_stats").count_documents({}),
    ))
    print("=" * 60)


# ============================== 各功能实现 ==============================
# 若环境无法输入中文，可直接输入类别编号代替
CATEGORIES = ["计算机", "文学", "数学", "经济管理", "外语"]


def choose_category():
    """选择图书类别：可直接输入 1~5 的编号，也可以输入类别名称。"""
    print("可选类别：" + " / ".join("%d.%s" % (i, n) for i, n in enumerate(CATEGORIES, start=1)))
    raw = input("请输入类别编号（或直接输入类别名称）：").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(CATEGORIES):
        return CATEGORIES[int(raw) - 1]
    return raw


def do_search_by_category(book_mgr):
    category = choose_category()
    if not category:
        print("提示：类别不能为空。")
        return
    show_books(book_mgr.search_by_category(category), "没有找到类别为「%s」的图书。" % category)


def do_search_by_price(book_mgr):
    try:
        low = float(input("请输入最低价：").strip())
        high = float(input("请输入最高价：").strip())
    except ValueError:
        print("提示：价格必须是数字。")
        return
    show_books(book_mgr.search_by_price_range(low, high),
               "没有找到价格在 %s ~ %s 元之间的图书。" % (low, high))


def do_find_by_isbn(book_mgr):
    isbn = input("请输入 13 位 ISBN：").strip()
    book = book_mgr.find_by_isbn(isbn)
    if book is None:
        print("提示：没有找到 ISBN 为 %s 的图书。" % isbn)
        return
    print("查询到 1 条记录：")
    for key in ("isbn", "title", "author", "publisher", "category", "price", "stock", "rating", "borrow_count"):
        value = book.get(key, "-")
        if key == "price":
            value = _num(value, "%.2f")
        elif key == "rating":
            value = _num(value, "%.1f")
        elif key in ("stock", "borrow_count"):
            value = _num(value, "%d")
        print("  %-12s : %s" % (key, value))


def do_add_book(book_mgr):
    isbn = input("ISBN（13 位）：").strip()
    title = input("书名：").strip()
    author = input("作者：").strip()
    publisher = input("出版社：").strip()
    category = input("类别：").strip()
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
        "tags": [category], "borrow_count": 0, "publish_date": datetime.now(),
    })
    print("新增成功，影响 1 条文档，_id = %s" % new_id)


def do_add_books(book_mgr):
    """批量新增 2 条演示图书（ISBN 用时间戳生成，避免与已有数据重复）。"""
    stamp = str(int(time.time()))
    demo = [
        {"isbn": "978" + stamp[:8] + "01", "title": "NoSQL 数据库原理", "author": "李工",
         "publisher": "高等教育出版社", "category": "计算机", "price": 69.8, "stock": 5,
         "rating": 4.3, "tags": ["计算机", "数据库"], "borrow_count": 0},
        {"isbn": "978" + stamp[:8] + "02", "title": "数据可视化实践", "author": "王敏",
         "publisher": "人民邮电出版社", "category": "计算机", "price": 79.0, "stock": 3,
         "rating": 4.1, "tags": ["计算机", "数据分析"], "borrow_count": 0},
    ]
    try:
        count = book_mgr.add_books(demo)
        print("批量新增完成，影响 %d 条文档。" % count)
        for book in demo:
            print("  isbn=%s  %s" % (book["isbn"], book["title"]))
    except Exception as exc:
        print("批量新增失败：%s" % exc)


def do_update_stock(book_mgr):
    isbn = input("请输入 ISBN：").strip()
    try:
        delta = int(input("请输入库存增减量（正数增加、负数减少）：").strip())
    except ValueError:
        print("提示：增减量必须是整数。")
        return
    matched, modified = book_mgr.update_stock(isbn, delta)
    if matched == 0:
        print("提示：没有找到 ISBN 为 %s 的图书，未更新任何文档。" % isbn)
        return
    print("更新完成，匹配 %d 条文档，实际修改 %d 条文档。" % (matched, modified))


def do_update_price_by_category(book_mgr):
    category = choose_category()
    try:
        ratio = float(input("请输入价格乘以的系数（如 0.9 表示打九折）：").strip())
    except ValueError:
        print("提示：系数必须是数字。")
        return
    matched, modified = book_mgr.update_price_by_category(category, ratio)
    if matched == 0:
        print("提示：类别「%s」下没有图书，未更新任何文档。" % category)
        return
    print("批量调价完成，匹配 %d 条文档，实际修改 %d 条文档。" % (matched, modified))


def do_delete_book(book_mgr):
    isbn = input("请输入要删除的 ISBN：").strip()
    deleted = book_mgr.delete_by_isbn(isbn)
    if deleted == 0:
        print("提示：没有找到 ISBN 为 %s 的图书，未删除任何文档。" % isbn)
        return
    print("删除完成，实际删除 %d 条文档。" % deleted)


def do_delete_by_category(book_mgr):
    category = choose_category()
    deleted = book_mgr.delete_by_category(category)
    if deleted == 0:
        print("提示：类别「%s」下没有图书，未删除任何文档。" % category)
        return
    print("批量删除完成，实际删除 %d 条文档。" % deleted)


def do_category_stats(stat_mgr):
    rows = stat_mgr.category_stats()
    if not rows:
        print("提示：没有统计数据。")
        return
    print("  %-10s %10s %12s %10s" % ("类别", "图书数量", "库存总量", "平均价格"))
    for row in rows:
        print("  %-10s %10d %12d %10.2f" % (
            row["_id"], row["图书数量"], row["库存总量"], row["平均价格"] or 0))


def do_borrow_trend(stat_mgr):
    rows = stat_mgr.borrow_trend()
    if not rows:
        print("提示：没有借阅记录。")
        return
    print("借阅趋势：")
    for row in rows:
        print("  %s ： %d 次" % (row["_id"], row["借阅量"]))


def do_best_sellers(stat_mgr):
    try:
        top_n = int(input("请输入榜单数量（如 5）：").strip())
    except ValueError:
        print("提示：数量必须是整数。")
        return
    rows = stat_mgr.best_sellers(top_n)
    if not rows:
        print("提示：没有图书数据。")
        return
    print("畅销榜 Top %d：" % top_n)
    for index, row in enumerate(rows, start=1):
        print("  第%d名  %-30s %-8s 借阅 %s 次" % (
            index, row.get("title", ""), row.get("category", "-"), row.get("borrow_count", "-")))


def do_reader_manage(reader_mgr):
    print("读者总数：%d" % reader_mgr.count())
    print("学院列表（distinct）：%s" % "、".join(reader_mgr.distinct_colleges()))
    print("等级列表（distinct）：%s" % "、".join(reader_mgr.distinct_levels()))
    print("各学院读者人数：")
    for row in reader_mgr.college_stats():
        print("  %-14s %d 人" % (row["_id"], row["人数"]))
    print("各等级读者人数：")
    for row in reader_mgr.level_stats():
        print("  %-8s %d 人" % (row["_id"], row["人数"]))


def do_borrow_book(borrow_mgr):
    reader_card = input("请输入读者借阅卡号（如 R20240001）：").strip()
    isbn = input("请输入图书 ISBN：").strip()
    log_id, matched, modified = borrow_mgr.borrow_book(reader_card, isbn)
    if log_id is None:
        print("提示：没有找到 ISBN 为 %s 的图书，借阅登记失败。" % isbn)
        return
    print("借阅登记成功，新增流水 1 条（_id=%s）。" % log_id)
    print("库存同步更新：匹配 %d 条文档，实际修改 %d 条文档。" % (matched, modified))
    book = borrow_mgr.books.find_one({"isbn": isbn}, {"title": 1, "stock": 1})
    print("图书「%s」当前剩余库存：%s" % (book.get("title"), book.get("stock")))


def do_return_books(borrow_mgr):
    raw = input("请输入要归还的 ISBN，多个用英文逗号分隔：").strip()
    isbn_list = [item.strip() for item in raw.split(",") if item.strip()]
    if not isbn_list:
        print("提示：至少要输入一个 ISBN。")
        return
    matched, modified = borrow_mgr.return_books(isbn_list)
    if matched == 0:
        print("提示：这些 ISBN 都没有对应的图书，未更新任何文档。")
        return
    print("归还处理完成，匹配 %d 条文档，实际修改 %d 条文档。" % (matched, modified))


def do_overdue(borrow_mgr):
    logs = borrow_mgr.overdue_list()
    if not logs:
        print("提示：当前没有逾期的借阅记录。")
        return
    print("逾期记录共 %d 条：" % len(logs))
    for log in logs:
        print("  读者 %-12s 图书 %-14s 状态 %s" % (
            log.get("reader_card", "-"), log.get("book_isbn", "-"), log.get("status", "-")))


# ============================== 主循环 ==============================
def main():
    if not dbc.test_connection():
        print("无法连接数据库，程序退出。请检查 MongoDB 服务是否已启动、账号密码是否正确。")
        sys.exit(1)

    book_mgr = BookManager(dbc.get_collection("books"))
    reader_mgr = ReaderManager(dbc.get_collection("readers"))
    borrow_mgr = BorrowManager(dbc.get_collection("books"), dbc.get_collection("borrow_logs"))
    stat_mgr = StatManager(dbc.get_collection("books"), dbc.get_collection("borrow_logs"))

    print_startup_info(book_mgr, reader_mgr, borrow_mgr)

    while True:
        print(MENU)
        choice = input("请选择功能编号：").strip()
        try:
            if choice == "0":
                break
            elif choice == "1":
                do_search_by_category(book_mgr)
            elif choice == "2":
                do_search_by_price(book_mgr)
            elif choice == "3":
                do_find_by_isbn(book_mgr)
            elif choice == "4":
                do_add_book(book_mgr)
            elif choice == "5":
                do_add_books(book_mgr)
            elif choice == "6":
                do_update_stock(book_mgr)
            elif choice == "7":
                do_update_price_by_category(book_mgr)
            elif choice == "8":
                do_delete_book(book_mgr)
            elif choice == "9":
                do_delete_by_category(book_mgr)
            elif choice == "10":
                do_category_stats(stat_mgr)
            elif choice == "11":
                do_borrow_trend(stat_mgr)
            elif choice == "12":
                do_best_sellers(stat_mgr)
            elif choice == "13":
                do_reader_manage(reader_mgr)
            elif choice == "14":
                do_borrow_book(borrow_mgr)
            elif choice == "15":
                do_return_books(borrow_mgr)
            elif choice == "16":
                do_overdue(borrow_mgr)
            else:
                print("提示：无效的编号，请重新选择。")
        except Exception as exc:
            print("操作出错：%s" % exc)
        print()

    dbc.close()
    print("数据库连接已关闭，程序退出。")


if __name__ == "__main__":
    main()
