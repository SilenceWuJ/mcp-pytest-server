#!/usr/bin/env python3
"""
检查MySQL中的测试结果
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_test_results():
    """检查测试结果"""
    mysql_url = "mysql+aiomysql://qa_user:123456@localhost:3306/qa_platform"
    
    print("检查MySQL中的测试结果...")
    
    try:
        engine = create_async_engine(
            mysql_url,
            echo=False,
            pool_pre_ping=True,
        )
        
        async with engine.connect() as conn:
            # 检查execution_results表
            print("\n1. 检查execution_results表:")
            result = await conn.execute(text("SELECT COUNT(*) FROM execution_results"))
            count = result.scalar()
            print(f"   总记录数: {count}")
            
            if count > 0:
                result = await conn.execute(text("SELECT * FROM execution_results ORDER BY id DESC LIMIT 5"))
                rows = result.fetchall()
                print(f"   最近5条记录:")
                for row in rows:
                    print(f"   - ID: {row.id}, 项目: {row.project_name}, 状态: {row.status}, 时间: {row.created_at}")
            
            # 检查projects表
            print("\n2. 检查projects表:")
            result = await conn.execute(text("SELECT COUNT(*) FROM projects"))
            count = result.scalar()
            print(f"   总记录数: {count}")
            
            if count > 0:
                result = await conn.execute(text("SELECT * FROM projects"))
                rows = result.fetchall()
                for row in rows:
                    print(f"   - ID: {row.id}, 名称: {row.name}, 描述: {row.description}")
            
            # 检查reports表
            print("\n3. 检查reports表:")
            result = await conn.execute(text("SELECT COUNT(*) FROM reports"))
            count = result.scalar()
            print(f"   总记录数: {count}")
            
            if count > 0:
                result = await conn.execute(text("SELECT * FROM reports ORDER BY id DESC LIMIT 3"))
                rows = result.fetchall()
                for row in rows:
                    print(f"   - ID: {row.id}, 执行ID: {row.execution_id}, 类型: {row.report_type}")
            
            # 检查表结构
            print("\n4. 表结构概览:")
            result = await conn.execute(text("""
                SELECT 
                    TABLE_NAME,
                    TABLE_ROWS,
                    DATA_LENGTH,
                    INDEX_LENGTH,
                    CREATE_TIME
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = 'qa_platform'
                ORDER BY TABLE_NAME
            """))
            tables = result.fetchall()
            
            print(f"   {'表名':<20} {'行数':<10} {'数据大小':<12} {'索引大小':<12} {'创建时间'}")
            print("   " + "-" * 70)
            for table in tables:
                table_name, rows, data_len, index_len, create_time = table
                data_mb = round(data_len / 1024 / 1024, 2) if data_len else 0
                index_mb = round(index_len / 1024 / 1024, 2) if index_len else 0
                print(f"   {table_name:<20} {rows:<10} {data_mb:<10}MB {index_mb:<10}MB {create_time}")
            
            await conn.close()
        
        await engine.dispose()
        
    except Exception as e:
        print(f"错误: {e}")

async def main():
    """主函数"""
    print("=" * 60)
    print("MySQL测试结果检查")
    print("=" * 60)
    
    await check_test_results()
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())