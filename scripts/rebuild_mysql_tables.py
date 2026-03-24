#!/usr/bin/env python3
"""
重建MySQL数据库表结构
支持测试用例、测试分析、HTML测试报告和项目详细信息
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# 导入模型
from src.database.models import Base
from src.database.connection import Database

async def drop_all_tables(engine):
    """删除所有表"""
    print("正在删除所有表...")
    async with engine.begin() as conn:
        # 获取所有表名
        result = await conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print(f"找到 {len(tables)} 个表: {', '.join(tables)}")
            # 禁用外键检查
            await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            for table in tables:
                print(f"  删除表: {table}")
                await conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            
            # 启用外键检查
            await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        else:
            print("数据库中没有表")
    
    print("所有表已删除")

async def create_all_tables(engine):
    """创建所有表"""
    print("正在创建所有表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("所有表已创建")

async def verify_tables(engine):
    """验证表结构"""
    print("验证表结构...")
    async with engine.begin() as conn:
        result = await conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"数据库中有 {len(tables)} 个表:")
        for table in tables:
            # 获取表结构
            result = await conn.execute(text(f"DESCRIBE `{table}`"))
            columns = result.fetchall()
            print(f"  {table} ({len(columns)} 列):")
            for col in columns:
                print(f"    - {col[0]}: {col[1]}")

async def test_connection(database_url):
    """测试数据库连接"""
    print(f"测试连接到: {database_url}")
    try:
        engine = create_async_engine(database_url, echo=True)
        async with engine.connect() as conn:
            # 测试连接
            result = await conn.execute(text("SELECT 1"))
            data = result.fetchone()
            print(f"✓ 连接成功: {data[0]}")
            
            # 获取数据库版本
            result = await conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"✓ MySQL版本: {version}")
            
        return engine
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return None

async def main():
    """主函数"""
    print("=" * 60)
    print("MySQL数据库表重建工具")
    print("=" * 60)
    
    # 数据库配置
    database_url = "mysql+pymysql://root:123456@localhost:3306/qa_platform"
    
    # 测试连接
    engine = await test_connection(database_url)
    if not engine:
        print("数据库连接失败，请检查配置")
        return
    
    try:
        # 删除所有表
        await drop_all_tables(engine)
        
        # 创建所有表
        await create_all_tables(engine)
        
        # 验证表结构
        await verify_tables(engine)
        
        print("\n" + "=" * 60)
        print("数据库表重建完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())