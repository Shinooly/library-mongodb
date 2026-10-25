// ============================================================
//  任务三 · 查询 / 更新 / 删除  完整操作日志
//  用法： mongosh library --file ~/task3_all.js
//  注意： 本脚本会改数据（U2 改价格、D 删除记录），只运行一次！
//  顺序： Q1-Q16 查询 → U1-U4 更新 → D1-D3 删除
// ============================================================

print("");
print("##########  任务三 · 基础检索 Q1-Q6  ##########");
print("Q1  db.books.find({price:{$gt:80}})                              => " + db.books.countDocuments({price:{$gt:80}}) + " 条");
print("Q2  db.books.find({stock:{$lt:10}})                              => " + db.books.countDocuments({stock:{$lt:10}}) + " 条");
print("Q3  db.books.find({isbn:{$eq:'9787115428028'}})                 => " + db.books.countDocuments({isbn:{$eq:"9787115428028"}}) + " 条");
print("Q4  db.readers.find({email:{$eq:null}})                         => " + db.readers.countDocuments({email:{$eq:null}}) + " 条");
print("Q5  db.books.find({publisher:{$ne:'人民邮电出版社'}})            => " + db.books.countDocuments({publisher:{$ne:"人民邮电出版社"}}) + " 条");
print("Q6  db.books.find({category:{$in:['计算机','经济管理']}})        => " + db.books.countDocuments({category:{$in:["计算机","经济管理"]}}) + " 条");

print("");
print("##########  任务三 · 组合与高级检索 Q7-Q12  ##########");
print("Q7  db.books.find({$and:[{rating:{$gt:4.0}},{category:'计算机'}]})  => " + db.books.countDocuments({$and:[{rating:{$gt:4.0}},{category:"计算机"}]}) + " 条");
print("Q8  db.books.find({$or:[{rating:{$lt:3.5}},{stock:0}]})          => " + db.books.countDocuments({$or:[{rating:{$lt:3.5}},{stock:0}]}) + " 条");
print("Q9  db.books.find({title:{$regex:'Python'}})                     => " + db.books.countDocuments({title:{$regex:"Python"}}) + " 条");
print("Q10 db.books.find({tags:{$all:['编程','入门']}})                  => " + db.books.countDocuments({tags:{$all:["编程","入门"]}}) + " 条");
print("Q11 db.books.find({tags:{$size:3}})                              => " + db.books.countDocuments({tags:{$size:3}}) + " 条");
print("Q12 db.books.find({tags:{$exists:true}})                         => " + db.books.countDocuments({tags:{$exists:true}}) + " 条");

print("");
print("##########  任务三 · 结果处理 Q13-Q16  ##########");
print("Q13 db.books.find({_id:{$type:'string'}})                        => " + db.books.countDocuments({_id:{$type:"string"}}) + " 条");
print("Q14 db.books.find().sort({rating:-1}).limit(5)                   => " + db.books.find().sort({rating:-1}).limit(5).toArray().length + " 条");
print("Q15 db.books.find({},{title:1,price:1,rating:1,_id:0})           => " + db.books.find({},{title:1,price:1,rating:1,_id:0}).toArray().length + " 条");
print("Q16 db.books.distinct('category')                                => " + db.books.distinct("category").length + " 个: " + db.books.distinct("category").join(" / "));

print("");
print("##########  任务三 · 更新 U1-U4  ##########");
var r;
r = db.books.updateOne({isbn:"9787115428028"}, {$inc:{stock:-5}});
print("U1  db.books.updateOne({isbn:'9787115428028'},{$inc:{stock:-5}})      => matched " + r.matchedCount + " / modified " + r.modifiedCount);
r = db.books.updateMany({category:"计算机"}, {$mul:{price:0.9}});
print("U2  db.books.updateMany({category:'计算机'},{$mul:{price:0.9}})        => matched " + r.matchedCount + " / modified " + r.modifiedCount);
r = db.books.updateOne({isbn:"9787115428028"}, {$currentDate:{last_updated:true}});
print("U3  db.books.updateOne({isbn:'9787115428028'},{$currentDate:{last_updated:true}}) => matched " + r.matchedCount + " / modified " + r.modifiedCount);
r = db.books.updateOne({isbn:"9787115428028"}, {$unset:{tags:""}});
print("U4  db.books.updateOne({isbn:'9787115428028'},{$unset:{tags:''}})    => matched " + r.matchedCount + " / modified " + r.modifiedCount);

print("");
print("##########  任务三 · 删除 D1-D3  ##########");
print("--- D2 预览查询（删除前，必须截图）---");
print("D2-preview  db.borrow_logs.find({status:'逾期'})                 => " + db.borrow_logs.countDocuments({status:"逾期"}) + " 条");
r = db.borrow_logs.deleteOne({status:{$eq:"已归还"}});
print("D1  db.borrow_logs.deleteOne({status:{$eq:'已归还'}})             => deleted " + r.deletedCount);
r = db.borrow_logs.deleteMany({status:"逾期"});
print("D2  db.borrow_logs.deleteMany({status:'逾期'}})                  => deleted " + r.deletedCount);
r = db.readers.replaceOne(
  {card_no:"R20240002"},
  {card_no:"R20240002", name:"李小雨", college:"经济管理学院", email:"lixiaoyu@example.edu",
   phone:"13900139000", level:"普通", register_date:new Date("2024-09-03"), fav_categories:["经济管理"]}
);
print("D3  db.readers.replaceOne({card_no:'R20240002'},{...})           => matched " + r.matchedCount + " / modified " + r.modifiedCount);
print("");
print("##########  任务三 执行完毕  ##########");
