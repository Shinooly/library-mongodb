// ====== 任务二 ST-2.1 + ST-2.2：建库与集合 ======
// 在 mongosh 中执行： mongosh library --file ~/task2_collections.js

// 清场（如果之前试过）
db.dropDatabase();

// --- 三个普通集合 ---
db.createCollection("books");
db.createCollection("readers");
db.createCollection("category_stats");

// --- 固定集合 book_logs：1MB，最多 1000 条 ---
db.createCollection("book_logs", {
  capped: true,
  size: 1048576,
  max: 1000
});

// --- 时间序列集合 borrow_logs ---
db.createCollection("borrow_logs", {
  timeseries: {
    timeField: "borrow_date",
    granularity: "hours"
  },
  expireAfterSeconds: 63072000
});

// --- 视图 book_in_stock：books 中 stock > 0 ---
db.createView("book_in_stock", "books", [
  { $match: { stock: { $gt: 0 } } }
]);

// ====== 验证 ======
print("=== collection list ===");
db.getCollectionNames();
print("=== book_logs options ===");
db.getCollectionInfos({name: "book_logs"})[0].options;
print("=== borrow_logs options ===");
db.getCollectionInfos({name: "borrow_logs"})[0].options;
print("=== book_in_stock options ===");
db.getCollectionInfos({name: "book_in_stock"})[0].options;
