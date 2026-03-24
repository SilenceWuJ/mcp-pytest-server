#!/usr/bin/env python3
"""
简单的MySQL连接测试
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_mysql_connection():
    """测试MySQL连接"""
    print("测试MySQL连接...")
    
    # 直接使用aiomysql测试
    try:
        import aiomysql
        
        # 测试连接参数
        config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'db': 'qa_platform',
            'charset': 'utf8mb4',
        }
        
        print(f"连接参数: {config['user']}@{config['host']}:{config['port']}/{config['db']}")
        
        # 创建连接池
        pool = await aiomysql.create_pool(**config)
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 测试查询
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                print(f"✓ MySQL连接成功: {result[0]}")
                
                # 获取版本
                await cur.execute("SELECT VERSION()")
                version = await cur.fetchone()
                print(f"✓ MySQL版本: {version[0]}")
                
                # 检查数据库
                await cur.execute("SHOW TABLES")
                tables = await cur.fetchall()
                print(f"✓ 数据库中有 {len(tables)} 个表")
                
                if tables:
                    print("现有表:")
                    for table in tables:
                        print(f"  - {table[0]}")
        
        pool.close()
        await pool.wait_closed()
        return True
        
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请安装: pip install aiomysql")
        return False
    except Exception as e:
        print(f"✗ MySQL连接失败: {e}")
        return False

async def test_sqlalchemy_connection():
    """测试SQLAlchemy连接"""
    print("\n测试SQLAlchemy连接...")
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # MySQL连接URL
        database_url = "mysql+aiomysql://root:123456@localhost:3306/qa_platform"
        print(f"连接URL: mysql+aiomysql://root:***@localhost:3306/qa_platform")
        
        # 创建引擎
        engine = create_async_engine(
            database_url,
            echo=True,
            pool_recycle=3600,
            pool_pre_ping=True,
        )
        
        async with engine.connect() as conn:
            # 测试查询
            result = await conn.execute(text("SELECT 1"))
            data = result.fetchone()
            print(f"✓ SQLAlchemy连接成功: {data[0]}")
            
            # 获取数据库信息
            result = await conn.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            print(f"✓ 当前数据库: {db_name}")
            
            # 检查表
            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"✓ 找到 {len(tables)} 个表")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ SQLAlchemy连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("MySQL连接测试")
    print("=" * 60)
    
    # 测试直接MySQL连接
    mysql_ok = await test_mysql_connection()
    
    # 测试SQLAlchemy连接
    sqlalchemy_ok = await test_sqlalchemy_connection()
    
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    
    if mysql_ok and sqlalchemy_ok:
        print("🎉 所有连接测试通过！")
        print("\n下一步:")
        print("1. 运行数据库初始化脚本: python scripts/rebuild_mysql_tables.py")
        print("2. 运行集成测试: python scripts/test_mysql_integration.py")
        return 0
    else:
        print("⚠️ 连接测试失败")
        print("\n可能的原因:")
        print("1. MySQL服务未启动")
        print("2. 数据库不存在: CREATE DATABASE qa_platform;")
        print("3. 用户权限不足")
        print("4. 网络连接问题")
        print("\n检查命令:")
        print("  sudo systemctl status mysql")
        print("  mysql -u root -p123456 -e 'SHOW DATABASES;'")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)