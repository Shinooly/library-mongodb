// ================= 任务三：索引创建与执行计划对比 =================
// 运行方式：mongosh "mongodb://127.0.0.1:27018/library_platform" --file scripts/task3_index.js
// 流程：先删掉 books 上的非 _id 索引并记录查询开销 -> 建立索引 -> 再记录一次

function statsOf(exp) {
  var st = exp.executionStats || {};
  return {
    nReturned: st.nReturned,
    docs: st.totalDocsExamined,
    keys: st.totalKeysExamined,
    ms: st.executionTimeMillis
  };
}

function showExp(label, exp) {
  var s = statsOf(exp);
  print("  " + label + "：返回 " + s.nReturned + " 条，扫描文档 " + s.docs +
        " 个，扫描索引键 " + s.keys + " 个，耗时 " + s.ms + " ms");
}

function dropNonIdIndexes(coll) {
  coll.getIndexes().forEach(function (ix) {
    if (ix.name !== "_id_") {
      coll.dropIndex(ix.name);
    }
  });
}

print("\n===== 1. 清理 books 上的旧索引 =====");
dropNonIdIndexes(db.books);
print("  当前索引：" + db.books.getIndexes().map(function (x) { return x.name; }).join(", "));

var query1 = { category: "计算机", price: { $gte: 50, $lte: 100 } };
var query2 = {};

print("\n===== 2. 建索引前的执行计划 =====");
showExp("Q1 类别+价格区间", db.books.find(query1).explain("executionStats"));
showExp("Q6 评分排序取前10", db.books.find(query2).sort({ rating: -1 }).limit(10).explain("executionStats"));

print("\n===== 3. 创建索引 =====");
db.books.createIndex({ isbn: 1 }, { unique: true, name: "uk_isbn" });
db.books.createIndex({ category: 1, price: 1 }, { name: "idx_category_price" });
db.books.createIndex({ tags: 1 }, { name: "idx_tags" });
db.books.createIndex({ rating: -1 }, { name: "idx_rating" });
db.books.createIndex({ publish_date: 1 }, { name: "idx_publish_date" });

print("\n===== 3.5 其余集合的索引（按任务二清单，无需前后对比）=====");
function tryIndex(coll, key, opt) {
  try { coll.createIndex(key, opt); print("  + " + opt.name + " 已创建"); }
  catch (e) { print("  ! " + opt.name + " 已存在：" + e.message.slice(0, 50)); }
}
tryIndex(db.books, { title: 1 }, { name: "idx_title" });
tryIndex(db.readers, { card_no: 1 }, { unique: true, name: "uk_card_no" });
tryIndex(db.readers, { college: 1 }, { name: "idx_college" });
tryIndex(db.borrow_logs, { book_isbn: 1 }, { name: "idx_book_isbn" });
print("  （borrow_logs 的 {reader_card, borrow_date} 复合索引已由时间序列集合自动创建）");

print("  已创建：" + db.books.getIndexes().map(function (x) { return x.name; }).join(", "));

print("\n===== 4. 建索引后的执行计划 =====");
showExp("Q1 类别+价格区间", db.books.find(query1).explain("executionStats"));
showExp("Q6 评分排序取前10", db.books.find(query2).sort({ rating: -1 }).limit(10).explain("executionStats"));

print("\n===== 5. 索引清单 =====");
db.books.getIndexes().forEach(function (ix) {
  print("  " + ix.name + "  key=" + JSON.stringify(ix.key) +
        (ix.unique ? "  unique" : ""));
});

print("\n===== 6. 唯一索引校验（重复 ISBN 应被拒绝） =====");
try {
  db.books.insertOne({
    isbn: "9787115428028", title: "重复ISBN测试", author: "测试", publisher: "测试",
    category: "计算机", price: 10.0, rating: 1.0, stock: 1, borrow_count: 0,
    publish_date: new Date("2024-01-01T00:00:00+08:00")
  });
  print("  未拦截，说明唯一索引有问题");
} catch (e) {
  print("  已拦截：" + e.message.slice(0, 80));
}

print("\n===== 索引与执行计划对比执行完毕 =====");
