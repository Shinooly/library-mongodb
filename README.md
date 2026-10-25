# 图书情报检索与统计平台（MongoDB 实训项目）

基于 MongoDB 的图书借阅管理系统，包含数据库建模、聚合统计、索引优化、权限管理和 PyMongo 控制台应用。

## 目录结构

```
├── app/                  PyMongo 控制台应用（任务五）
│   ├── mongodb_connect.py  数据库连接封装（连接串统一在此维护）
│   ├── book_manager.py     图书增删改查、批量调价
│   ├── reader_manager.py   读者信息与分类统计
│   ├── borrow_manager.py   借阅登记、归还、逾期查询
│   ├── stat_manager.py     分类统计、借阅趋势、畅销榜
│   └── main.py             主菜单（16 项功能）
├── scripts/              建库与演练脚本
│   ├── task2_collections.js  创建固定集合、时间序列集合、视图
│   ├── task2_import.sh       用 mongoimport 导入三份数据
│   ├── task3_all.js          查询 / 更新 / 删除共 23 条操作
│   ├── task4a.js             聚合统计 A1–A9
│   └── task4b.js             索引 I1–I5 与 explain 对比
└── backup/               mongodump 导出的数据库备份
```

## 环境

- MongoDB 8.0.32 / mongosh 2.12.0
- Python 3.12 + pymongo 4.18.3
- CentOS Stream 10（虚拟机）

## 使用

1. 恢复数据库：

```bash
mongorestore --db library --authenticationDatabase library -u libWriter -p <密码> backup/
```

2. 运行控制台应用：

```bash
cd app
python main.py
```

3. 连接参数在 `app/mongodb_connect.py` 中集中配置（地址、端口、账号、authSource）。

## 数据说明

- `books`：24 条图书，含 ISBN 唯一索引、类别索引、标签多键索引、类别+价格复合索引
- `readers`：16 条读者
- `borrow_logs`：时间序列集合（timeField=borrow_date，granularity=hours），保留期 5 年
- `book_logs`：固定集合（capped，1 MB / 1000 条上限）
- `book_in_stock`：视图，只展示库存大于 0 的图书
- `category_stats`：聚合结果集合，由 `$merge` 写入的 5 条分类统计

## 账号

- `libReader`：只读权限（read）
- `libWriter`：读写 + 库管理权限（readWrite、dbAdmin）
