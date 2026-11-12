"""
GridFS 文件存储模块
----------------
负责电子书 PDF 与封面图的上传、清单查询、按书名下载与字节数校验。

每个文件写入以下元数据：
    related_isbn   关联图书 ISBN
    file_type      ebook（电子书）/ cover（封面）
    original_name  原始文件名
"""

import json
import os
import re

from gridfs import GridFS


class GridfsManager:
    """封装 GridFS 的上传、查询与下载。"""

    def __init__(self, db, books):
        self.db = db
        self.books = books
        self.fs = GridFS(db)

    def upload_manifest(self, manifest_path, files_dir):
        """
        按清单批量上传，返回 [(文件名, 结果说明)]。
        同名文件已存在时跳过，避免重复上传。
        """
        with open(manifest_path, "r", encoding="utf-8") as fp:
            manifest = json.load(fp)

        report = []
        for key, file_type in (("ebooks", "ebook"), ("covers", "cover")):
            for item in manifest.get(key, []):
                name = item.get("filename")
                path = os.path.join(files_dir, name)
                if not os.path.isfile(path):
                    report.append((name, "文件不存在，已跳过"))
                    continue
                if self.fs.exists({"filename": name}):
                    report.append((name, "已存在，已跳过"))
                    continue
                with open(path, "rb") as fp:
                    self.fs.put(
                        fp,
                        filename=name,
                        metadata={
                            "related_isbn": item.get("related_isbn"),
                            "file_type": file_type,
                            "original_name": name,
                        },
                    )
                report.append((name, "上传成功，%d 字节" % os.path.getsize(path)))
        return report

    def list_files(self):
        """列出 GridFS 中全部文件（文件名、大小、上传时间、元数据）。"""
        rows = []
        for f in self.fs.find().sort("uploadDate", 1):
            meta = f.metadata or {}
            rows.append({
                "filename": f.filename,
                "length": f.length,
                "upload_date": f.upload_date,
                "file_type": meta.get("file_type", "-"),
                "related_isbn": meta.get("related_isbn", "-"),
            })
        return rows

    def find_by_title(self, title):
        """
        按书名查图书及其电子书。
        返回 (图书文档或 None, [GridOut 列表])。
        """
        book = self.books.find_one(
            {"title": {"$regex": re.escape(title), "$options": "i"}},
            {"_id": 0, "title": 1, "isbn": 1, "ebook_name": 1}
        )
        if book is None:
            return None, []
        ebook_name = book.get("ebook_name")
        if not ebook_name:
            return book, []
        return book, list(self.fs.find({"filename": ebook_name}))

    def download_by_title(self, title, dest_dir):
        """
        按书名下载电子书到本地，并校验字节数。
        返回说明字典；找不到图书或电子书时 status 标明原因。
        """
        book, files = self.find_by_title(title)
        if book is None:
            return {"status": "no_book"}
        if not files:
            return {"status": "no_ebook", "book": book}

        grid_out = files[0]
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, grid_out.filename)
        with open(dest_path, "wb") as fp:
            fp.write(grid_out.read())

        downloaded = os.path.getsize(dest_path)
        return {
            "status": "ok",
            "book": book,
            "filename": grid_out.filename,
            "stored_bytes": grid_out.length,
            "downloaded_bytes": downloaded,
            "match": downloaded == grid_out.length,
            "path": dest_path,
        }
