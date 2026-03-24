"""
数据库连接管理 - 新版
支持MySQL、SQLite、PostgreSQL，支持HTML报告和测试分析
"""
import asyncio
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool, StaticPool
from sqlalchemy import text
import logging

from ..config import settings
from .models import Base

logger = logging.getLogger(__name__)


class Database:
    """数据库连接管理器"""
    
    def __init__(self, database_url: Optional[str] = None, **kwargs):
        """
        初始化数据库连接
        
        Args:
            database_url: 数据库连接URL
            **kwargs: 额外配置参数
        """
        self.database_url = database_url or settings.database_url
        self.config = kwargs
        
        # 转换同步驱动为异步驱动
        self._convert_to_async_url()
        
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[sessionmaker] = None
        
        logger.info(f"初始化数据库连接: {self._masked_url()}")
    
    def _convert_to_async_url(self):
        """转换同步驱动URL为异步驱动URL"""
        if self.database_url.startswith("sqlite"):
            # SQLite -> aiosqlite
            self.database_url = self.database_url.replace(
                "sqlite://", "sqlite+aiosqlite://"
            )
        elif self.database_url.startswith("mysql"):
            # MySQL -> aiomysql
            if "mysql+pymysql://" in self.database_url:
                self.database_url = self.database_url.replace(
                    "mysql+pymysql://", "mysql+aiomysql://"
                )
            elif "mysql://" in self.database_url:
                self.database_url = self.database_url.replace(
                    "mysql://", "mysql+aiomysql://"
                )
        elif self.database_url.startswith("postgresql"):
            # PostgreSQL -> asyncpg
            if "postgresql://" in self.database_url:
                self.database_url = self.database_url.replace(
                    "postgresql://", "postgresql+asyncpg://"
                )
    
    def _masked_url(self) -> str:
        """返回脱敏的数据库URL（隐藏密码）"""
        if "@" in self.database_url:
            # 提取协议和主机部分
            protocol_part = self.database_url.split("://")[0] + "://"
            host_part = self.database_url.split("@")[-1]
            return f"{protocol_part}***:***@{host_part}"
        return self.database_url
    
    def _get_pool_config(self) -> Dict[str, Any]:
        """获取连接池配置"""
        if "mysql" in self.database_url:
            return {
                "poolclass": QueuePool,
                "pool_size": self.config.get("pool_size", 5),
                "max_overflow": self.config.get("max_overflow", 10),
                "pool_timeout": self.config.get("pool_timeout", 30),
                "pool_recycle": self.config.get("pool_recycle", 3600),
                "pool_pre_ping": True,
                "connect_args": {
                    "charset": "utf8mb4",
                    "use_unicode": True,
                }
            }
        elif "postgresql" in self.database_url:
            return {
                "poolclass": QueuePool,
                "pool_size": self.config.get("pool_size", 5),
                "max_overflow": self.config.get("max_overflow", 10),
                "pool_timeout": self.config.get("pool_timeout", 30),
                "pool_recycle": self.config.get("pool_recycle", 3600),
                "pool_pre_ping": True,
            }
        else:  # SQLite
            return {
                "poolclass": NullPool,
                "connect_args": {"check_same_thread": False},
            }
    
    async def connect(self, create_tables: bool = True):
        """连接数据库"""
        if self.engine is not None:
            logger.warning("数据库已连接，跳过重复连接")
            return
        
        try:
            pool_config = self._get_pool_config()
            
            self.engine = create_async_engine(
                self.database_url,
                echo=settings.debug,
                **pool_config,
            )
            
            # 创建会话工厂
            self.async_session_maker = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            
            # 测试连接
            await self._test_connection()
            
            # 创建表
            if create_tables:
                await self.create_tables()
            
            logger.info(f"数据库连接成功: {self._masked_url()}")
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            self.engine = None
            self.async_session_maker = None
            raise
    
    async def _test_connection(self):
        """测试数据库连接"""
        async with self.engine.connect() as conn:
            if "mysql" in self.database_url:
                result = await conn.execute(text("SELECT 1"))
                await conn.execute(text("SET NAMES utf8mb4"))
                await conn.execute(text("SET CHARACTER SET utf8mb4"))
                await conn.execute(text("SET character_set_connection=utf8mb4"))
            elif "postgresql" in self.database_url:
                result = await conn.execute(text("SELECT 1"))
            else:  # SQLite
                result = await conn.execute(text("SELECT 1"))
            
            data = result.fetchone()
            logger.debug(f"数据库连接测试: {data[0]}")
    
    async def create_tables(self, drop_existing: bool = False):
        """创建数据库表
        
        Args:
            drop_existing: 是否删除已存在的表
        """
        if not self.engine:
            raise RuntimeError("数据库未连接，请先调用connect()方法")
        
        async with self.engine.begin() as conn:
            if drop_existing:
                logger.warning("删除所有已存在的表...")
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.info("创建数据库表...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建完成")
    
    async def drop_tables(self):
        """删除所有数据库表"""
        if not self.engine:
            raise RuntimeError("数据库未连接，请先调用connect()方法")
        
        async with self.engine.begin() as conn:
            logger.warning("删除所有数据库表...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("数据库表删除完成")
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.async_session_maker = None
            logger.info("数据库连接已断开")
    
    def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        if self.async_session_maker is None:
            raise RuntimeError("数据库未连接，请先调用connect()方法")
        return self.async_session_maker()
    
    async def execute_raw_sql(self, sql: str, params: Optional[Dict] = None) -> Any:
        """执行原始SQL语句
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            执行结果
        """
        async with self.get_session() as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()
            return result
    
    async def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        if not self.engine:
            return {"status": "disconnected"}
        
        try:
            async with self.engine.connect() as conn:
                if "mysql" in self.database_url:
                    # MySQL信息
                    version_result = await conn.execute(text("SELECT VERSION()"))
                    version = version_result.scalar()
                    
                    db_result = await conn.execute(text("SELECT DATABASE()"))
                    database = db_result.scalar()
                    
                    return {
                        "status": "connected",
                        "type": "mysql",
                        "version": version,
                        "database": database,
                        "url": self._masked_url(),
                    }
                elif "postgresql" in self.database_url:
                    # PostgreSQL信息
                    version_result = await conn.execute(text("SELECT version()"))
                    version = version_result.scalar()
                    
                    db_result = await conn.execute(text("SELECT current_database()"))
                    database = db_result.scalar()
                    
                    return {
                        "status": "connected",
                        "type": "postgresql",
                        "version": version,
                        "database": database,
                        "url": self._masked_url(),
                    }
                else:  # SQLite
                    version_result = await conn.execute(text("SELECT sqlite_version()"))
                    version = version_result.scalar()
                    
                    return {
                        "status": "connected",
                        "type": "sqlite",
                        "version": version,
                        "url": self._masked_url(),
                    }
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "url": self._masked_url(),
            }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()


# 全局数据库实例
db = Database()


async def get_database() -> Database:
    """获取数据库实例"""
    return db


async def init_database(database_url: Optional[str] = None, **kwargs):
    """初始化数据库
    
    Args:
        database_url: 数据库连接URL
        **kwargs: 额外配置参数
    """
    global db
    
    if database_url:
        db = Database(database_url, **kwargs)
    
    await db.connect()
    
    # 记录数据库信息
    info = await db.get_database_info()
    logger.info(f"数据库初始化完成: {info}")


async def close_database():
    """关闭数据库连接"""
    await db.disconnect()


async def recreate_database(drop_existing: bool = True):
    """重新创建数据库（删除并重建所有表）
    
    Args:
        drop_existing: 是否删除已存在的表
    """
    await db.connect(create_tables=False)
    
    if drop_existing:
        await db.drop_tables()
    
    await db.create_tables()
    logger.info("数据库重建完成")


async def check_database_health() -> Dict[str, Any]:
    """检查数据库健康状态"""
    try:
        info = await db.get_database_info()
        
        if info["status"] == "connected":
            # 测试查询
            async with db.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                test_result = result.scalar()
                
                return {
                    "healthy": True,
                    "status": "connected",
                    "test_result": test_result,
                    "info": info,
                }
        else:
            return {
                "healthy": False,
                "status": info["status"],
                "error": info.get("error"),
                "info": info,
            }
    except Exception as e:
        return {
            "healthy": False,
            "status": "error",
            "error": str(e),
        }