#!/usr/bin/env python3
"""
数据库功能测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, TestRun, TestCase
from src.database.connection import get_database_url
from src.database.crud import (
    create_test_run,
    create_test_case,
    get_test_run,
    get_test_runs,
    update_test_run,
    get_test_cases_by_run,
)


async def test_database_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    
    db_url = get_database_url()
    print(f"数据库URL: {db_url}")
    
    engine = create_async_engine(db_url, echo=False)
    
    try:
        async with engine.connect() as conn:
            # 测试连接
            result = await conn.execute("SELECT 1")
            data = result.fetchone()
            if data and data[0] == 1:
                print("✓ 数据库连接成功")
                return True
            else:
                print("✗ 数据库连接测试失败")
                return False
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False
    finally:
        await engine.dispose()


async def test_create_tables():
    """测试创建表"""
    print("\n测试创建表...")
    
    db_url = get_database_url()
    engine = create_async_engine(db_url, echo=False)
    
    try:
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✓ 表创建成功")
            
            # 验证表是否存在
            result = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            tables = result.fetchall()
            table_names = [t[0] for t in tables]
            
            expected_tables = ["test_runs", "test_cases", "projects"]
            for table in expected_tables:
                if table in table_names:
                    print(f"  ✓ 表 '{table}' 存在")
                else:
                    print(f"  ✗ 表 '{table}' 不存在")
                    
            return all(table in table_names for table in expected_tables)
            
    except Exception as e:
        print(f"✗ 表创建失败: {e}")
        return False
    finally:
        await engine.dispose()


async def test_crud_operations():
    """测试CRUD操作"""
    print("\n测试CRUD操作...")
    
    db_url = get_database_url()
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # 1. 创建测试运行记录
            print("1. 创建测试运行记录...")
            test_run = await create_test_run(
                session=session,
                project_name="test_project",
                test_path="tests/test_example.py",
                total_tests=10,
                passed=8,
                failed=1,
                skipped=1,
                duration=5.5,
                status="completed"
            )
            
            if test_run and test_run.id:
                print(f"  ✓ 创建成功, ID: {test_run.id}")
                run_id = test_run.id
            else:
                print("  ✗ 创建失败")
                return False
            
            # 2. 创建测试用例记录
            print("2. 创建测试用例记录...")
            test_cases = []
            for i in range(3):
                test_case = await create_test_case(
                    session=session,
                    run_id=run_id,
                    test_name=f"test_example_{i}",
                    status="passed" if i < 2 else "failed",
                    duration=0.5 + i * 0.1,
                    error_message="Test failed" if i == 2 else None,
                    stack_trace="Traceback..." if i == 2 else None
                )
                test_cases.append(test_case)
                print(f"  ✓ 创建测试用例 {i+1}, ID: {test_case.id}")
            
            # 3. 查询测试运行记录
            print("3. 查询测试运行记录...")
            retrieved_run = await get_test_run(session, run_id)
            if retrieved_run:
                print(f"  ✓ 查询成功, 项目: {retrieved_run.project_name}")
                print(f"    状态: {retrieved_run.status}, 持续时间: {retrieved_run.duration}s")
                print(f"    通过: {retrieved_run.passed}, 失败: {retrieved_run.failed}, 跳过: {retrieved_run.skipped}")
            else:
                print("  ✗ 查询失败")
                return False
            
            # 4. 更新测试运行记录
            print("4. 更新测试运行记录...")
            updated_run = await update_test_run(
                session=session,
                run_id=run_id,
                status="completed",
                duration=6.0
            )
            if updated_run:
                print(f"  ✓ 更新成功, 新状态: {updated_run.status}, 新持续时间: {updated_run.duration}s")
            else:
                print("  ✗ 更新失败")
                return False
            
            # 5. 查询测试用例
            print("5. 查询测试用例...")
            cases = await get_test_cases_by_run(session, run_id)
            if cases:
                print(f"  ✓ 查询到 {len(cases)} 个测试用例")
                for case in cases:
                    print(f"    - {case.test_name}: {case.status} ({case.duration}s)")
            else:
                print("  ✗ 查询失败")
                return False
            
            # 6. 查询测试运行列表
            print("6. 查询测试运行列表...")
            runs = await get_test_runs(session, project_name="test_project")
            if runs:
                print(f"  ✓ 查询到 {len(runs)} 个测试运行")
                for run in runs:
                    print(f"    - ID: {run.id}, 状态: {run.status}, 创建时间: {run.created_at}")
            else:
                print("  ✗ 查询失败")
                return False
            
            print("\n✓ 所有CRUD操作测试通过!")
            return True
            
    except Exception as e:
        print(f"✗ CRUD操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def test_foreign_key_constraint():
    """测试外键约束"""
    print("\n测试外键约束...")
    
    db_url = get_database_url()
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # 尝试创建引用不存在的run_id的测试用例
            print("1. 测试无效外键引用...")
            try:
                test_case = await create_test_case(
                    session=session,
                    run_id=99999,  # 不存在的run_id
                    test_name="invalid_test",
                    status="failed",
                    duration=0.0
                )
                print("  ✗ 应该抛出外键约束错误")
                return False
            except Exception as e:
                if "foreign key" in str(e).lower() or "constraint" in str(e).lower():
                    print("  ✓ 外键约束生效")
                else:
                    print(f"  ✗ 意外的错误: {e}")
                    return False
            
            # 测试级联删除
            print("2. 测试级联删除...")
            # 先创建一个测试运行和关联的测试用例
            test_run = await create_test_run(
                session=session,
                project_name="cascade_test",
                test_path="tests/cascade.py",
                status="completed"
            )
            
            test_case = await create_test_case(
                session=session,
                run_id=test_run.id,
                test_name="cascade_test_case",
                status="passed"
            )
            
            # 删除测试运行
            from src.database.crud import delete_test_run
            deleted = await delete_test_run(session, test_run.id)
            if deleted:
                print("  ✓ 测试运行删除成功")
                
                # 检查关联的测试用例是否也被删除
                cases = await get_test_cases_by_run(session, test_run.id)
                if not cases:
                    print("  ✓ 关联的测试用例已级联删除")
                else:
                    print("  ✗ 关联的测试用例未被删除")
                    return False
            else:
                print("  ✗ 测试运行删除失败")
                return False
            
            print("\n✓ 外键约束测试通过!")
            return True
            
    except Exception as e:
        print(f"✗ 外键约束测试失败: {e}")
        return False
    finally:
        await engine.dispose()


async def main():
    """主测试函数"""
    print("=" * 60)
    print("数据库功能测试")
    print("=" * 60)
    
    results = []
    
    # 测试数据库连接
    results.append(("数据库连接", await test_database_connection()))
    
    # 测试创建表
    results.append(("表创建", await test_create_tables()))
    
    # 测试CRUD操作
    results.append(("CRUD操作", await test_crud_operations()))
    
    # 测试外键约束
    results.append(("外键约束", await test_foreign_key_constraint()))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过!")
    else:
        print("✗ 部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)