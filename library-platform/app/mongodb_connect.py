"""
数据库连接模块
----------------
统一封装 MongoDB 的连接与库、集合获取逻辑，供其他模块调用。

连接参数全部来自环境变量，默认连本机 library 库：
    MONGO_URI  例：mongodb://libWriter:密码@127.0.0.1:27017/library?authSource=library
    MONGO_DB   默认 library

这样在单机、副本集（mongodb://host1,host2,host3/library?replicaSet=rs0）
或通过 mongos 连接分片集群时，都不用改代码，只换连接串即可。
"""

import os
from datetime import timedelta, timezone

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/library_platform")
DB_NAME = os.getenv("MONGO_DB", "library_platform")
TIMEOUT_MS = 5000
LOCAL_TZ = timezone(timedelta(hours=8))

_client = None


def get_client():
    """获取（并复用）MongoClient 实例。"""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=TIMEOUT_MS,
                              tz_aware=True, tzinfo=LOCAL_TZ)
    return _client


def get_db():
    """获取项目数据库对象。"""
    return get_client()[DB_NAME]


def get_collection(name):
    """获取指定集合对象。"""
    return get_db()[name]


def test_connection():
    """测试连接是否可用，成功返回 True。"""
    try:
        get_db().command("ping")
        return True
    except Exception as exc:
        print("数据库连接失败：%s" % exc)
        return False


def close():
    """关闭连接。"""
    global _client
    if _client is not None:
        _client.close()
        _client = None
