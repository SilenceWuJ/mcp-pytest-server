#!/usr/bin/env python3
"""
数据库初始化脚本
创建数据库表结构
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.database.models import Base
from src.database.connection import get_database_url


async def init_database():
    """初始化数据库，创建所有表"""
    print("正在初始化数据库...")
    
    # 获取数据库URL
    db_url = get_database_url()
    print(f"数据库URL: {db_url}")
    
    # 创建异步引擎
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    try:
        # 创建所有表
        async with engine.begin() as conn:
            print("正在创建表...")
            await conn.run_sync(Base.metadata.create_all)
            print("表创建完成!")
        
        # 显示创建的表
        async with engine.connect() as conn:
            result = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            tables = result.fetchall()
            print("\n已创建的表:")
            for table in tables:
                print(f"  - {table[0]}")
        
        print("\n数据库初始化完成!")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


async def drop_database():
    """删除所有表（用于测试）"""
    print("警告: 正在删除所有表...")
    
    db_url = get_database_url()
    engine = create_async_engine(db_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("所有表已删除!")
    except Exception as e:
        print(f"删除表失败: {e}")
    finally:
        await engine.dispose()


async def check_database():
    """检查数据库状态"""
    print("检查数据库状态...")
    
    db_url = get_database_url()
    engine = create_async_engine(db_url, echo=False)
    
    try:
        async with engine.connect() as conn:
            # 检查表是否存在
            result = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            tables = result.fetchall()
            
            if tables:
                print("\n现有表:")
                for table in tables:
                    print(f"  - {table[0]}")
                    
                    # 显示表结构
                    result2 = await conn.execute(f"PRAGMA table_info({table[0]});")
                    columns = result2.fetchall()
                    for col in columns:
                        print(f"    * {col[1]} ({col[2]})")
            else:
                print("数据库中没有表")
                
    except Exception as e:
        print(f"检查数据库失败: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument("action", choices=["init", "drop", "check"], 
                       help="操作: init-初始化, drop-删除所有表, check-检查状态")
    
    args = parser.parse_args()
    
    if args.action == "init":
        asyncio.run(init_database())
    elif args.action == "drop":
        confirm = input("确认删除所有表? (yes/no): ")
        if confirm.lower() == "yes":
            asyncio.run(drop_database())
        else:
            print("操作取消")
    elif args.action == "check":
        asyncio.run(check_database())