#!/usr/bin/env python3
"""
测试MySQL数据库连接
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_mysql_connection():
    """测试MySQL连接"""
    # 使用配置中的MySQL URL
    mysql_url = "mysql+aiomysql://qa_user:123456@localhost:3306/qa_platform"
    
    print(f"尝试连接到MySQL: {mysql_url}")
    
    try:
        # 创建异步引擎
        engine = create_async_engine(
            mysql_url,
            echo=True,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # 测试连接
        async with engine.connect() as conn:
            print("✓ 数据库连接成功!")
            
            # 执行一个简单的查询
            result = await conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"✓ MySQL版本: {version}")
            
            # 检查数据库是否存在
            result = await conn.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            print(f"✓ 当前数据库: {db_name}")
            
            # 检查表是否存在
            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"✓ 数据库中的表: {len(tables)} 个")
            
            if tables:
                print("  表列表:")
                for table in tables:
                    print(f"  - {table[0]}")
            
            await conn.close()
        
        await engine.dispose()
        print("✓ 连接测试完成!")
        return True
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        print("\n可能的原因:")
        print("1. MySQL服务未启动")
        print("2. 用户名/密码错误")
        print("3. 数据库不存在")
        print("4. 网络连接问题")
        print("\n请检查:")
        print(f"  - MySQL服务状态: sudo systemctl status mysql")
        print(f"  - 数据库是否存在: CREATE DATABASE qa_platform;")
        print(f"  - 用户权限: GRANT ALL ON qa_platform.* TO 'qa_user'@'localhost';")
        return False

async def test_sqlite_fallback():
    """测试SQLite回退连接"""
    print("\n尝试SQLite回退连接...")
    sqlite_url = "sqlite+aiosqlite:///./test_results.db"
    
    try:
        engine = create_async_engine(
            sqlite_url,
            echo=True,
        )
        
        async with engine.connect() as conn:
            print("✓ SQLite连接成功!")
            
            # 检查SQLite版本
            result = await conn.execute(text("SELECT sqlite_version()"))
            version = result.scalar()
            print(f"✓ SQLite版本: {version}")
            
            await conn.close()
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ SQLite连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("数据库连接测试")
    print("=" * 60)
    
    # 测试MySQL连接
    mysql_success = await test_mysql_connection()
    
    if not mysql_success:
        print("\nMySQL连接失败，尝试SQLite回退...")
        await test_sqlite_fallback()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())