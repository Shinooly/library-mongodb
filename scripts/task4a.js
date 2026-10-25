// ================= 任务四 A1—A9 聚合统计 =================
// 运行方式（终端里）：mongosh library --file ~/task4a.js

function title(t) { print("\n===== " + t + " ====="); }

// ---------- A1 ----------
title("A1 按类别统计图书数量与平均评分  [$group + $sum + $avg]");
print('db.books.aggregate([{$group:{_id:"$category",cnt:{$sum:1},avgRating:{$avg:"$rating"}}},{$sort:{cnt:-1}}])');
db.books.aggregate([
  { $group: { _id: "$category", "cnt": { $sum: 1 }, "avgRating": { $avg: "$rating" } } },
  { $sort: { "cnt": -1 } }
]).forEach(function (d) {
  print("  " + d._id + " : 数量=" + d["cnt"] + "  平均评分=" + d["avgRating"].toFixed(2));
});

// ---------- A2 ----------
title("A2 各出版社图书数量，取最多的 5 家  [$group + $topN]");
print('db.books.aggregate([{$group:{_id:"$publisher",cnt:{$sum:1}}},{$group:{_id:null,top5:{$topN:{n:5,sortBy:{cnt:-1},output:"$$ROOT"}}}}])');
db.books.aggregate([
  { $group: { _id: "$publisher", "cnt": { $sum: 1 } } },
  { $group: { _id: null, "top5": { $topN: { n: 5, sortBy: { "cnt": -1 }, output: "$$ROOT" } } } }
]).forEach(function (d) {
  d["top5"].forEach(function (x, i) { print("  第" + (i + 1) + "名  " + x._id + " : " + x["cnt"] + " 种"); });
});

// ---------- A3 ----------
title("A3 文档数最多的图书类别  [$sortByCount]");
print('db.books.aggregate([{$sortByCount:"$category"}])');
db.books.aggregate([{ $sortByCount: "$category" }]).forEach(function (d) {
  print("  " + d._id + " : " + d.count + " 本");
});

// ---------- A4 ----------
title("A4 评分最高的 3 本图书  [$sort + $limit + $project]");
print('db.books.aggregate([{$sort:{rating:-1}},{$limit:3},{$project:{_id:0,title:1,rating:1,borrow_count:1}}])');
db.books.aggregate([
  { $sort: { "rating": -1 } },
  { $limit: 3 },
  { $project: { _id: 0, "title": 1, "rating": 1, "borrow_count": 1 } }
]).forEach(function (d) {
  print("  " + d.title + "  评分=" + d.rating + "  借阅次数=" + d.borrow_count);
});

// ---------- A5 ----------
title("A5 每本书销售额 = 单价 x 借阅次数，四舍五入两位  [$multiply + $round]");
print('db.books.aggregate([{$project:{_id:0,title:1,sales:{$round:[{$multiply:["$price","$borrow_count"]},2]}}},{$sort:{sales:-1}}])');
db.books.aggregate([
  { $project: { _id: 0, "title": 1,
      "sales": { $round: [ { $multiply: [ "$price", "$borrow_count" ] }, 2 ] } } },
  { $sort: { "sales": -1 } }
]).forEach(function (d) {
  print("  " + d.title + " : " + d.sales);
});

// ---------- A6 ----------
title("A6 按借阅年份分组统计借阅量  [$year + $dateToString]");
print('db.borrow_logs.aggregate([{$group:{_id:{y:{$year:"$borrow_date"},s:{$dateToString:{format:"%Y年",date:"$borrow_date"}}},cnt:{$sum:1}}},{$sort:{"_id.y":1}}])');
db.borrow_logs.aggregate([
  { $group: { _id: { "y": { $year: "$borrow_date" },
                      "s": { $dateToString: { format: "%Y年", date: "$borrow_date" } } },
              "cnt": { $sum: 1 } } },
  { $sort: { "_id.y": 1 } }
]).forEach(function (d) {
  print("  " + d._id["s"] + " : " + d["cnt"] + " 次");
});

// ---------- A7 ----------
title("A7 每位读者借阅次数，取前 5 名  [$group + $sort + $limit]");
print('db.borrow_logs.aggregate([{$group:{_id:"$reader_card",cnt:{$sum:1}}},{$sort:{cnt:-1}},{$limit:5}])');
db.borrow_logs.aggregate([
  { $group: { _id: "$reader_card", "cnt": { $sum: 1 } } },
  { $sort: { "cnt": -1 } },
  { $limit: 5 }
]).forEach(function (d) {
  print("  " + d._id + " : " + d["cnt"] + " 次");
});

// ---------- A8 ----------
title("A8 关联读者与借阅流水，学院借阅量排行榜  [$lookup]");
print('db.readers.aggregate([{$lookup:{from:"borrow_logs",localField:"card_no",foreignField:"reader_card",as:"logs"}},{$unwind:"$logs"},{$group:{_id:"$college",cnt:{$sum:1}}},{$sort:{cnt:-1}}])');
db.readers.aggregate([
  { $lookup: { from: "borrow_logs", localField: "card_no", foreignField: "reader_card", as: "logs" } },
  { $unwind: "$logs" },
  { $group: { _id: "$college", "cnt": { $sum: 1 } } },
  { $sort: { "cnt": -1 } }
]).forEach(function (d) {
  print("  " + d._id + " : " + d["cnt"] + " 次");
});

// ---------- A9 ----------
title("A9 把 A1 的分类统计结果写入 category_stats 集合  [$merge]");
print('db.books.aggregate([{$group:{_id:"$category",cnt:{$sum:1},avgRating:{$avg:"$rating"}}},{$merge:{into:"category_stats",whenMatched:"replace",whenNotMatched:"insert"}}])');
db.books.aggregate([
  { $group: { _id: "$category", "cnt": { $sum: 1 }, "avgRating": { $avg: "$rating" } } },
  { $merge: { into: "category_stats", whenMatched: "replace", whenNotMatched: "insert" } }
]);
print("  写入完成，category_stats 现有 " + db.category_stats.countDocuments() + " 条记录：");
db.category_stats.find().forEach(function (d) {
  print("  " + d._id + " : 数量=" + d["cnt"] + "  平均评分=" + d["avgRating"].toFixed(2));
});

print("\n===== A1—A9 全部执行完毕 =====");
