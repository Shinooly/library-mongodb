"""
数据库连接模块
----------------
统一封装 MongoDB 的连接与库、集合获取逻辑，被后续所有功能模块调用。

作者：__________    日期：__________
"""

from pymongo import MongoClient

# ============================ 连接参数（统一定义在本模块内） ============================
MONGO_HOST = "127.0.0.1"
MONGO_PORT = 27017
MONGO_USER = "libWriter"
MONGO_PASSWORD = "shy060225"
AUTH_SOURCE = "library"
DB_NAME = "library"
TIMEOUT_MS = 3000

_client = None


def get_client():
    """获取（并复用）MongoClient 实例。"""
    global _client
    if _client is None:
        uri = "mongodb://%s:%s@%s:%d/%s?authSource=%s" % (
            MONGO_USER, MONGO_PASSWORD, MONGO_HOST, MONGO_PORT, DB_NAME, AUTH_SOURCE
        )
        _client = MongoClient(uri, serverSelectionTimeoutMS=TIMEOUT_MS)
    return _client


def get_db():
    """获取 library 数据库对象。"""
    return get_client()[DB_NAME]


def get_collection(name):
    """获取指定集合对象。"""
    return get_db()[name]


def test_connection():
    """测试数据库连接是否可用，成功返回 True，失败返回 False。"""
    try:
        get_db().command("ping")
        return True
    except Exception as exc:
        print("数据库连接失败：%s" % exc)
        return False


def close():
    """关闭数据库连接。"""
    global _client
    if _client is not None:
        _client.close()
        _client = None
