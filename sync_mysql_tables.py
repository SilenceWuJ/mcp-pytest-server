#!/usr/bin/env python3
"""
同步MySQL数据库表结构
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect

async def check_existing_tables():
    """检查现有表结构"""
    mysql_url = "mysql+aiomysql://qa_user:123456@localhost:3306/qa_platform"
    
    print("检查MySQL现有表结构...")
    
    engine = create_async_engine(
        mysql_url,
        echo=False,
        pool_pre_ping=True,
    )
    
    try:
        async with engine.connect() as conn:
            # 获取所有表
            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            print(f"\n数据库中有 {len(tables)} 个表:")
            for table in tables:
                table_name = table[0]
                print(f"\n表: {table_name}")
                
                # 获取表结构
                result = await conn.execute(text(f"DESCRIBE {table_name}"))
                columns = result.fetchall()
                
                print(f"  列数: {len(columns)}")
                for col in columns:
                    col_name, col_type, null, key, default, extra = col
                    print(f"  - {col_name}: {col_type} {'(PK)' if key == 'PRI' else ''} {'(NULL)' if null == 'YES' else '(NOT NULL)'}")
            
            await conn.close()
        
        return True
        
    except Exception as e:
        print(f"检查表结构失败: {e}")
        return False
    finally:
        await engine.dispose()

async def create_required_tables():
    """创建应用需要的表"""
    mysql_url = "mysql+aiomysql://qa_user:123456@localhost:3306/qa_platform"
    
    print("\n创建应用需要的表...")
    
    engine = create_async_engine(
        mysql_url,
        echo=True,
        pool_pre_ping=True,
    )
    
    try:
        async with engine.connect() as conn:
            # 检查test_runs表是否存在
            result = await conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'qa_platform' 
                AND table_name = 'test_runs'
            """))
            test_runs_exists = result.scalar() > 0
            
            if not test_runs_exists:
                print("创建 test_runs 表...")
                await conn.execute(text("""
                    CREATE TABLE test_runs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        project_name VARCHAR(255) NOT NULL,
                        test_path VARCHAR(500) NOT NULL,
                        total_tests INT DEFAULT 0,
                        passed INT DEFAULT 0,
                        failed INT DEFAULT 0,
                        skipped INT DEFAULT 0,
                        duration FLOAT DEFAULT 0.0,
                        status VARCHAR(50) DEFAULT 'pending',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_project_name (project_name),
                        INDEX idx_created_at (created_at)
                    )
                """))
                print("✓ test_runs 表创建成功")
            else:
                print("✓ test_runs 表已存在")
            
            # 检查test_cases表是否存在
            result = await conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'qa_platform' 
                AND table_name = 'test_cases'
            """))
            test_cases_exists = result.scalar() > 0
            
            if not test_cases_exists:
                print("创建 test_cases 表...")
                await conn.execute(text("""
                    CREATE TABLE test_cases (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        run_id INT NOT NULL,
                        test_name VARCHAR(500) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        duration FLOAT DEFAULT 0.0,
                        error_message TEXT,
                        stack_trace TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_run_id (run_id),
                        INDEX idx_test_name (test_name),
                        FOREIGN KEY (run_id) REFERENCES test_runs(id) ON DELETE CASCADE
                    )
                """))
                print("✓ test_cases 表创建成功")
            else:
                print("✓ test_cases 表已存在")
            
            # 检查projects表是否存在（应用版本）
            result = await conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'qa_platform' 
                AND table_name = 'projects'
            """))
            projects_exists = result.scalar() > 0
            
            if projects_exists:
                # 检查projects表结构
                result = await conn.execute(text("DESCRIBE projects"))
                columns = result.fetchall()
                column_names = [col[0] for col in columns]
                
                # 检查是否缺少应用需要的列
                required_columns = ['default_test_path', 'default_pytest_options', 'environment_vars', 'is_active']
                missing_columns = [col for col in required_columns if col not in column_names]
                
                if missing_columns:
                    print(f"projects表缺少列: {missing_columns}")
                    # 这里可以添加ALTER TABLE语句来添加缺失的列
                else:
                    print("✓ projects表结构完整")
            else:
                print("projects表已存在（但可能是其他结构）")
            
            await conn.commit()
            await conn.close()
        
        print("\n✅ 表结构同步完成!")
        return True
        
    except Exception as e:
        print(f"创建表失败: {e}")
        return False
    finally:
        await engine.dispose()

async def test_table_operations():
    """测试表操作"""
    mysql_url = "mysql+aiomysql://qa_user:123456@localhost:3306/qa_platform"
    
    print("\n测试表操作...")
    
    engine = create_async_engine(
        mysql_url,
        echo=True,
        pool_pre_ping=True,
    )
    
    try:
        async with engine.connect() as conn:
            # 插入测试数据到test_runs
            print("插入测试数据到test_runs...")
            await conn.execute(text("""
                INSERT INTO test_runs (project_name, test_path, total_tests, passed, failed, skipped, duration, status)
                VALUES ('test_project', 'tests/test_example.py', 10, 8, 1, 1, 5.25, 'completed')
            """))
            
            # 获取插入的ID
            result = await conn.execute(text("SELECT LAST_INSERT_ID()"))
            run_id = result.scalar()
            print(f"插入的test_run ID: {run_id}")
            
            # 插入测试数据到test_cases
            print("插入测试数据到test_cases...")
            await conn.execute(text("""
                INSERT INTO test_cases (run_id, test_name, status, duration)
                VALUES (:run_id, 'test_example_1', 'passed', 1.5)
            """), {"run_id": run_id})
            
            await conn.execute(text("""
                INSERT INTO test_cases (run_id, test_name, status, duration, error_message)
                VALUES (:run_id, 'test_example_2', 'failed', 2.0, 'AssertionError: Expected 2, got 1')
            """), {"run_id": run_id})
            
            # 查询数据
            print("\n查询test_runs数据:")
            result = await conn.execute(text("SELECT * FROM test_runs ORDER BY id DESC LIMIT 1"))
            row = result.fetchone()
            if row:
                print(f"  ID: {row[0]}, 项目: {row[1]}, 状态: {row[8]}, 通过: {row[4]}/{row[3]}")
            
            print("\n查询test_cases数据:")
            result = await conn.execute(text("SELECT * FROM test_cases WHERE run_id = :run_id"), {"run_id": run_id})
            cases = result.fetchall()
            for case in cases:
                print(f"  ID: {case[0]}, 测试名: {case[2]}, 状态: {case[3]}")
            
            await conn.commit()
            await conn.close()
        
        print("\n✅ 表操作测试成功!")
        return True
        
    except Exception as e:
        print(f"表操作测试失败: {e}")
        return False
    finally:
        await engine.dispose()

async def main():
    """主函数"""
    print("=" * 60)
    print("MySQL数据库表结构同步")
    print("=" * 60)
    
    # 检查现有表结构
    await check_existing_tables()
    
    # 创建需要的表
    success = await create_required_tables()
    
    if success:
        # 测试表操作
        await test_table_operations()
    
    print("\n" + "=" * 60)
    print("同步完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())