# """
# 数据库连接管理
# """
# import asyncio
# from typing import Optional
# from sqlalchemy.ext.asyncio import (
#     AsyncSession,
#     async_sessionmaker,
#     create_async_engine,
#     AsyncEngine,
# )
# from sqlalchemy.orm import declarative_base
# from sqlalchemy.pool import NullPool
#
# from ..config import settings
# from .models import Base
#
#
# class Database:
#     """数据库连接管理器"""
#
#     def __init__(self, database_url: Optional[str] = None):
#         self.database_url = database_url or settings.database_url
#
#         # 转换SQLite URL为异步版本
#         if self.database_url.startswith("sqlite"):
#             self.database_url = self.database_url.replace(
#                 "sqlite://", "sqlite+aiosqlite://"
#             )
#
#         self.engine: Optional[AsyncEngine] = None
#         self.async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
#
#     async def connect(self):
#         """连接数据库"""
#         if self.engine is None:
#             # 创建异步引擎
#             self.engine = create_async_engine(
#                 self.database_url,
#                 echo=settings.debug,
#                 poolclass=NullPool,  # SQLite使用NullPool
#                 connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
#             )
#
#             # 创建会话工厂
#             self.async_session_maker = async_sessionmaker(
#                 self.engine,
#                 class_=AsyncSession,
#                 expire_on_commit=False,
#             )
#
#             # 创建表
#             await self.create_tables()
#
#     async def create_tables(self):
#         """创建数据库表"""
#         async with self.engine.begin() as conn:
#             await conn.run_sync(Base.metadata.create_all)
#
#     async def disconnect(self):
#         """断开数据库连接"""
#         if self.engine:
#             await self.engine.dispose()
#             self.engine = None
#             self.async_session_maker = None
#
#     def get_session(self) -> AsyncSession:
#         """获取数据库会话"""
#         if self.async_session_maker is None:
#             raise RuntimeError("数据库未连接，请先调用connect()方法")
#         return self.async_session_maker()
#
#     async def __aenter__(self):
#         """异步上下文管理器入口"""
#         await self.connect()
#         return self
#
#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         """异步上下文管理器出口"""
#         await self.disconnect()
#
#
# # 全局数据库实例
# db = Database()
#
#
# async def get_database() -> Database:
#     """获取数据库实例"""
#     return db
#
#
# async def init_database():
#     """初始化数据库"""
#     await db.connect()
#
#
# async def close_database():
#     """关闭数据库连接"""
#     await db.disconnect()


"""
数据库连接管理 (支持 MySQL / SQLite)
"""
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from ..config import settings
from .models import Base


class Database:
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url

        # 转换同步驱动为异步驱动
        if self.database_url.startswith("sqlite"):
            self.database_url = self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
        elif self.database_url.startswith("mysql"):
            # 支持 mysql:// 或 mysql+pymysql:// 格式
            self.database_url = self.database_url.replace("mysql://", "mysql+aiomysql://")
            self.database_url = self.database_url.replace("mysql+pymysql://", "mysql+aiomysql://")

        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[sessionmaker] = None

    async def connect(self):
        if self.engine is None:
            # 根据数据库类型选择连接池和参数
            if "mysql" in self.database_url:
                poolclass = QueuePool
                connect_args = {
                    "charset": "utf8mb4",
                    "use_unicode": True,
                }
                # 从配置读取连接池参数（假设 settings 有 pool 配置）
                pool_kwargs = {
                    "pool_size": getattr(settings, 'pool_size', 5),
                    "max_overflow": getattr(settings, 'max_overflow', 10),
                    "pool_timeout": getattr(settings, 'pool_timeout', 30),
                    "pool_recycle": getattr(settings, 'pool_recycle', 3600),
                    "pool_pre_ping": True,
                }
            else:  # SQLite
                poolclass = NullPool
                connect_args = {"check_same_thread": False}
                pool_kwargs = {}

            self.engine = create_async_engine(
                self.database_url,
                echo=settings.debug,
                poolclass=poolclass,
                **pool_kwargs,
                connect_args=connect_args,
            )

            self.async_session_maker = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            await self.create_tables()

    async def create_tables(self):
        """创建数据库表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def disconnect(self):
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.async_session_maker = None

    def get_session(self) -> AsyncSession:
        if self.async_session_maker is None:
            raise RuntimeError("数据库未连接，请先调用connect()方法")
        return self.async_session_maker()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


db = Database()

async def get_database() -> Database:
    return db

async def init_database():
    await db.connect()

async def close_database():
    await db.disconnect()

# async def init_database():
#     await db.connect()
#
# async def close_database():
#     await db.disconnect()