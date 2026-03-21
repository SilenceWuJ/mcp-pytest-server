#!/usr/bin/env python3
"""
简单检查MySQL表结构
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_tables():
    """检查表结构"""
    mysql_url = "mysql+aiomysql://qa_user:123456@localhost:3306/qa_platform"
    
    print("检查MySQL表结构...")
    
    try:
        engine = create_async_engine(
            mysql_url,
            echo=False,
            pool_pre_ping=True,
        )
        
        async with engine.connect() as conn:
            # 列出所有表
            print("\n1. 数据库中的所有表:")
            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            for i, table in enumerate(tables, 1):
                table_name = table[0]
                print(f"   {i}. {table_name}")
                
                # 检查每个表的结构
                result = await conn.execute(text(f"DESCRIBE {table_name}"))
                columns = result.fetchall()
                print(f"     列数: {len(columns)}")
                
                # 显示前几列
                for col in columns[:3]:
                    print(f"     - {col[0]} ({col[1]})")
                if len(columns) > 3:
                    print(f"     ... 还有 {len(columns)-3} 列")
                print()
            
            # 检查是否有测试数据
            print("\n2. 检查测试数据:")
            
            # 检查execution_results表
            result = await conn.execute(text("SELECT * FROM execution_results LIMIT 1"))
            if result.rowcount > 0:
                print("   ✓ execution_results表中有数据")
                # 显示列名
                columns = result.keys()
                print(f"     列: {', '.join(columns)}")
            else:
                print("   ✗ execution_results表中没有数据")
            
            # 检查projects表
            result = await conn.execute(text("SELECT * FROM projects LIMIT 1"))
            if result.rowcount > 0:
                print("   ✓ projects表中有数据")
                columns = result.keys()
                print(f"     列: {', '.join(columns)}")
            else:
                print("   ✗ projects表中没有数据")
            
            await conn.close()
        
        await engine.dispose()
        
    except Exception as e:
        print(f"错误: {e}")

async def main():
    """主函数"""
    print("=" * 60)
    print("MySQL表结构检查")
    print("=" * 60)
    
    await check_tables()
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())