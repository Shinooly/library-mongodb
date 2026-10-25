#!/bin/bash
echo "=== import books ==="
mongoimport --db library --collection books --file ~/books.txt --jsonArray
echo ""
echo "=== import readers ==="
mongoimport --db library --collection readers --file ~/readers.txt --jsonArray
echo ""
echo "=== import borrow_logs (timeseries) ==="
mongoimport --db library --collection borrow_logs --file ~/borrow_logs.txt --jsonArray
echo ""
echo "=== doc counts ==="
mongosh library --quiet --eval "print('books:', db.books.countDocuments()); print('readers:', db.readers.countDocuments()); print('borrow_logs:', db.borrow_logs.countDocuments()); print('book_logs:', db.book_logs.countDocuments()); print('category_stats:', db.category_stats.countDocuments())"
echo ""
echo "=== insertOne demo (ST-2.3 requires it) ==="
mongosh library --quiet --eval '
db.books.insertOne({
  isbn: "9787000000001",
  title: "MongoDB实战",
  author: "张三",
  publisher: "机械工业出版社",
  category: "计算机",
  price: 79.0,
  stock: 10,
  rating: 4.5,
  tags: ["MongoDB", "数据库"],
  publish_date: new Date("2024-01-01"),
  borrow_count: 0
});
print("books after insertOne:", db.books.countDocuments());
'
