// ================= 任务四 I1—I5 索引建立与验证 =================
// 运行方式（终端里）：mongosh library --file ~/task4b.js

function title(t) { print("\n===== " + t + " ====="); }

// ---------- I1 ----------
title("I1 为 books.isbn 建立唯一索引，并验证重复 ISBN 无法插入");
print('db.books.createIndex({isbn:1},{unique:true,name:"uk_isbn"})');
print("  返回索引名 => " + db.books.createIndex({ isbn: 1 }, { unique: true, name: "uk_isbn" }));

var one = db.books.findOne({}, { isbn: 1 });
print("  取出一个已存在的 isbn = " + one.isbn + " ，用它再插一条新文档：");
try {
  db.books.insertOne({
    isbn: one.isbn, title: "重复ISBN测试", author: "测试", publisher: "测试",
    category: "测试", price: 1, stock: 1, rating: 1, tags: [], borrow_count: 0
  });
  print("  !! 竟然插入成功，说明唯一索引未生效，需要检查");
} catch (e) {
  print("  插入被拒绝 => " + e.message);
}
print("  （出现 E11000 duplicate key error 即唯一索引生效）");

// ---------- I2 ----------
title("I2 为 books.title 建立单键索引");
print('db.books.createIndex({title:1})');
print("  返回索引名 => " + db.books.createIndex({ title: 1 }, { name: "idx_title" }));

// ---------- I3 ----------
title("I3 为 books.category 建立单键索引");
print('db.books.createIndex({category:1})');
print("  返回索引名 => " + db.books.createIndex({ category: 1 }, { name: "idx_category" }));

// ---------- I4 ----------
title("I4 为 books.tags 建立多键索引（数组字段）");
print('db.books.createIndex({tags:1})');
print("  返回索引名 => " + db.books.createIndex({ tags: 1 }, { name: "idx_tags" }));

// ---------- I5 ----------
title("I5 为 category 与 price 建立组合索引（复合索引）");
print('db.books.createIndex({category:1,price:-1})');
print("  返回索引名 => " + db.books.createIndex({ category: 1, price: -1 }, { name: "idx_category_price" }));

// ---------- 索引清单 ----------
title("索引清单 db.books.getIndexes()");
printjson(db.books.getIndexes());

// ---------- explain 对比 ----------
title('explain("executionStats") 对比：走索引 vs 全表扫描');
print('db.books.find({category:"计算机"}).hint({category:1,price:-1}).explain("executionStats")');
print('db.books.find({category:"计算机"}).hint({$natural:1}).explain("executionStats")');
var cond = { category: "计算机" };
var withIdx = db.books.find(cond).hint({ category: 1, price: -1 }).explain("executionStats").executionStats;
var noIdx = db.books.find(cond).hint({ $natural: 1 }).explain("executionStats").executionStats;
print("  [走索引]   扫描文档数=" + withIdx.totalDocsExamined + "  返回文档数=" + withIdx.nReturned + "  耗时=" + withIdx.executionTimeMillis + " ms");
print("  [全表扫描] 扫描文档数=" + noIdx.totalDocsExamined + "  返回文档数=" + noIdx.nReturned + "  耗时=" + noIdx.executionTimeMillis + " ms");
print("  （扫描文档数越少、耗时越短，说明索引越有效）");

print("\n===== I1—I5 全部执行完毕 =====");
