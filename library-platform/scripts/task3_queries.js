// ================= 任务三：11 项检索与统计 =================
// 运行方式：
//   mongosh "mongodb://127.0.0.1:27017/library" --file scripts/task3_queries.js
//   开启认证时把连接串换成 mongodb://libWriter:密码@127.0.0.1:27017/library?authSource=library
// 每条都会打印结果数量，方便直接抄进实验记录。

function sec(t) { print("\n===== " + t + " ====="); }

// ---------------- 检索 1：类别 + 价格区间 ----------------
sec("Q1 按类别与价格区间组合筛选（计算机 / 50-100 元）");
var r1 = db.books.find(
  { category: "计算机", price: { $gte: 50, $lte: 100 } },
  { _id: 0, title: 1, category: 1, price: 1 }
).toArray();
print("Q1 结果数量：" + r1.length + " 条");
r1.slice(0, 5).forEach(function (d) { print("  " + d.title + "  " + d.price + " 元"); });

// ---------------- 检索 2：标签多选匹配 ----------------
sec("Q2 同时包含多个标签（编程 + Python）");
var r2 = db.books.find({ tags: { $all: ["编程", "Python"] } }, { _id: 0, title: 1, tags: 1 }).toArray();
print("Q2 结果数量：" + r2.length + " 条");
r2.slice(0, 5).forEach(function (d) { print("  " + d.title + "  " + d.tags.join("/")); });

// ---------------- 检索 3：书名模糊检索 ----------------
sec("Q3 书名模糊检索（含 Python，不区分大小写）");
var r3 = db.books.find({ title: /python/i }, { _id: 0, title: 1, author: 1 }).toArray();
print("Q3 结果数量：" + r3.length + " 条");
r3.slice(0, 5).forEach(function (d) { print("  " + d.title + "  " + d.author); });

// ---------------- 检索 4：出版年份范围 ----------------
sec("Q4 按出版年份范围检索（2018-2020 年）");
var r4 = db.books.aggregate([
  { $match: { publish_date: {
      $gte: new Date("2018-01-01T00:00:00+08:00"),
      $lt: new Date("2021-01-01T00:00:00+08:00")
  } } },
  { $project: { _id: 0, title: 1, publish_date: {
      $dateToString: { format: "%Y-%m-%d", date: "$publish_date", timezone: "+08:00" }
  } } },
  { $sort: { publish_date: 1 } }
]).toArray();
print("Q4 结果数量：" + r4.length + " 条");
r4.slice(0, 5).forEach(function (d) { print("  " + d.title + "  " + d.publish_date); });

// ---------------- 检索 5：缺少 tags 字段 ----------------
sec("Q5 数据质量核查：缺少 tags 字段的图书");
var r5 = db.books.find({ tags: { $exists: false } }, { _id: 0, isbn: 1, title: 1 }).toArray();
print("Q5 结果数量：" + r5.length + " 条");
r5.forEach(function (d) { print("  " + d.isbn + "  " + d.title); });

// ---------------- 检索 6：评分前 10 ----------------
sec("Q6 评分排序取前 10（仅返回书名、作者、评分）");
var r6 = db.books.find({}, { _id: 0, title: 1, author: 1, rating: 1 })
  .sort({ rating: -1 }).limit(10).toArray();
print("Q6 结果数量：" + r6.length + " 条");
r6.forEach(function (d, i) { print("  第" + (i + 1) + "名 " + d.title + "  " + d.author + "  " + d.rating); });

// ---------------- 统计 1：分类统计 ----------------
sec("S1 按类别统计藏书量、平均价格、平均评分");
var s1 = db.books.aggregate([
  { $group: {
      _id: "$category",
      total_stock: { $sum: "$stock" },
      avg_price: { $avg: "$price" },
      avg_rating: { $avg: "$rating" },
      book_count: { $sum: 1 }
  } },
  { $sort: { total_stock: -1 } }
]).toArray();
print("S1 结果数量：" + s1.length + " 个类别");
s1.forEach(function (d) {
  print("  " + d._id + "：藏书量=" + d.total_stock + "  均价=" + d.avg_price.toFixed(2) +
        "  平均评分=" + d.avg_rating.toFixed(2) + "  书目数=" + d.book_count);
});

// ---------------- 统计 2：学院借阅总量前 5 ----------------
sec("S2 各学院借阅总量，取前 5 名（$lookup 关联）");
var s2 = db.readers.aggregate([
  { $lookup: { from: "borrow_logs", localField: "card_no", foreignField: "reader_card", as: "logs" } },
  { $unwind: "$logs" },
  { $group: { _id: "$college", borrow_total: { $sum: 1 } } },
  { $sort: { borrow_total: -1 } },
  { $limit: 5 }
]).toArray();
print("S2 结果数量：" + s2.length + " 个学院（取前 5）");
s2.forEach(function (d, i) { print("  第" + (i + 1) + "名 " + d._id + "：" + d.borrow_total + " 次"); });

// ---------------- 统计 3：按年月借阅趋势 ----------------
sec("S3 按年月统计借阅趋势（可读标签）");
var s3 = db.borrow_logs.aggregate([
  { $group: {
      _id: { $dateToString: { format: "%Y年%m月", date: "$borrow_date", timezone: "+08:00" } },
      borrow_total: { $sum: 1 }
  } },
  { $sort: { _id: 1 } }
]).toArray();
print("S3 结果数量：" + s3.length + " 个月份");
s3.forEach(function (d) { print("  " + d._id + "：" + d.borrow_total + " 次"); });

// ---------------- 统计 4：借阅最多的 10 本 + 馆藏位置 ----------------
sec("S4 借阅次数最多的 10 本图书，并带出馆藏位置");
var s4 = db.books.find({}, { _id: 0, title: 1, category: 1, borrow_count: 1, location: 1 })
  .sort({ borrow_count: -1 }).limit(10).toArray();
print("S4 结果数量：" + s4.length + " 本");
s4.forEach(function (d, i) {
  var loc = d.location || {};
  print("  第" + (i + 1) + "名 " + d.title + "：" + d.borrow_count + " 次，位置 " +
        (loc.floor || "-") + " / " + (loc.shelf || "-") + " / 复本 " + (loc.copies || "-"));
});

// ---------------- 统计 5：分类统计写入新集合 ----------------
sec("S5 把分类统计结果写入 category_stats 集合（$merge）");
db.books.aggregate([
  { $group: {
      _id: "$category",
      total_stock: { $sum: "$stock" },
      avg_price: { $avg: "$price" },
      avg_rating: { $avg: "$rating" },
      book_count: { $sum: 1 }
  } },
  { $merge: { into: "category_stats", whenMatched: "replace", whenNotMatched: "insert" } }
]);
print("S5 写入后 category_stats 共 " + db.category_stats.countDocuments() + " 条记录");
db.category_stats.find({}, { _id: 1, book_count: 1, total_stock: 1 }).forEach(function (d) {
  print("  " + d._id + "：" + d.book_count + " 本，藏书量 " + d.total_stock);
});

print("\n===== 任务三 11 项检索统计执行完毕 =====");
