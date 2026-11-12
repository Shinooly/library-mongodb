# 04-过程记录截图 / C —— 图形化验收（Compass）

本目录是「成员 C：图形化验收」的交付物，对应任务七的三项要求：
Compass 连库并核对集合数据量、一次聚合查询的图形化结果与命令行比对、导出统计结果文件。

## 一、文件清单

| 文件 | 内容 |
|---|---|
| `01_Compass连接与集合数据量.png` | Compass 已连接 `127.0.0.1:27017`，`library_platform` 库 5 个集合的文档数（books 50、readers 30、category_stats 6、audit_logs 0） |
| `02_borrow_logs文档数3000.png` | `borrow_logs`（时间序列集合）集合页，分页显示 `1 – 25 of 3000` |
| `03_Compass聚合查询结果.png` | 在 `books` 上执行 `$group` + `$sort` 管道，界面显示 `Showing 1 – 6 count results` 及 6 条明细 |
| `04_命令行同管道结果.png` | mongosh 执行同一条管道的输出，用于与上一张逐行比对 |
| `category_stats.json` | 程序菜单 12 导出的分类统计结果（6 条，含 category 字段） |
| `比对说明.md` | 集合数据量核对表、聚合结果三处（界面 / 命令行 / JSON）比对表与验收结论 |

## 二、环境

- MongoDB **8.3.11**，单机实例，端口 `27017`，数据目录自选（本次用 `E:\mongo-gui\data`）
- MongoDB Compass **1.53.0**
- mongosh **2.13.0**
- 数据库 `library_platform`，端口与库名与文档中的单机环境一致

## 三、复现步骤

```bash
# 1. 启动单机实例
mongod --dbpath E:\mongo-gui\data --port 27017 --bind_ip 127.0.0.1

# 2. 导入三份数据（books 50 / readers 30 / borrow_logs 3000）
python library-platform/scripts/data_clean.py --uri mongodb://127.0.0.1:27017/library_platform

# 3. 生成并导出分类统计（程序菜单 11 写入、菜单 12 导出）
python -c "import sys; sys.path.insert(0,'library-platform/app'); import mongodb_connect as d; from stat_manager import StatManager as S; m=S(d.get_collection('books'),d.get_collection('borrow_logs'),d.get_collection('readers'),d.get_collection('category_stats')); print(m.save_category_stats()); print(m.export_category_stats('library-platform/exports/category_stats.json'))"
```

Compass 端：

1. 连接串填 `mongodb://127.0.0.1:27017/library_platform`，点 Connect；
2. 左侧点开 `library_platform` → 看到 5 个集合与文档数（对应 `01`）；
3. 点 `borrow_logs` → 顶部分页显示 `1 – 25 of 3000`（对应 `02`）；
4. 点 `books` → `Aggregations` 选项卡 → 切到 `TEXT` 模式，粘贴：

```javascript
[
  { "$group": {
      "_id": "$category",
      "total_stock": { "$sum": "$stock" },
      "avg_price": { "$avg": "$price" },
      "avg_rating": { "$avg": "$rating" },
      "book_count": { "$sum": 1 }
  } },
  { "$sort": { "total_stock": -1 } }
]
```

5. 点 `Run`，结果区显示 6 条（对应 `03`）；
6. 命令行执行同一条管道（对应 `04`）：

```javascript
db.books.aggregate([{$group:{_id:"$category",total_stock:{$sum:"$stock"},
  avg_price:{$avg:"$price"},avg_rating:{$avg:"$rating"},book_count:{$sum:1}}},
  {$sort:{total_stock:-1}}]).toArray()
```

7. 菜单 12 导出的 `category_stats.json` 复制到本目录，作为交付文件。

## 四、截图说明

- 截图取自 Compass 窗口（屏幕 2880×1800，200% 缩放），已裁掉底部任务栏；
- 第 3 张为显示全部 6 条结果，把 Compass 界面缩放到 75%，因此字号略小，但内容完整可读；
- 三张截图与两张命令行/JSON 结果同属一次运行（2026-11-11 23:37—23:47），数据未做任何手工修改。
