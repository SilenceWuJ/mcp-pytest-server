#!/usr/bin/env python3
"""
MySQL集成测试脚本
测试数据库连接、表创建、CRUD操作和HTML报告存储
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection_new import Database, init_database, recreate_database
from src.database.crud_new import (
    create_project, get_project_by_name, get_projects,
    create_test_run, update_test_run_results, get_test_run,
    create_test_case, create_test_cases_batch, get_test_cases_by_run,
    create_html_report, get_html_reports_by_run,
    create_test_analysis, get_test_analyses_by_run,
    get_project_statistics, get_flaky_tests,
)
from src.database.models import TestRunStatus, TestCaseStatus


async def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("1. 测试数据库连接")
    print("=" * 60)
    
    # 使用MySQL配置
    database_url = "mysql+pymysql://root:123456@localhost:3306/qa_platform"
    
    try:
        db = Database(database_url)
        await db.connect()
        
        # 获取数据库信息
        info = await db.get_database_info()
        print(f"数据库信息: {json.dumps(info, indent=2, ensure_ascii=False)}")
        
        await db.disconnect()
        print("✓ 数据库连接测试通过")
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False


async def test_recreate_tables():
    """测试重建表结构"""
    print("\n" + "=" * 60)
    print("2. 测试重建数据库表")
    print("=" * 60)
    
    try:
        await recreate_database(drop_existing=True)
        print("✓ 数据库表重建成功")
        return True
    except Exception as e:
        print(f"✗ 数据库表重建失败: {e}")
        return False


async def test_project_crud():
    """测试项目CRUD操作"""
    print("\n" + "=" * 60)
    print("3. 测试项目CRUD操作")
    print("=" * 60)
    
    db = Database()
    await db.connect()
    
    try:
        async with db.get_session() as session:
            # 创建项目
            print("创建测试项目...")
            project = await create_project(
                session=session,
                name="test-project-1",
                description="测试项目1 - 用于集成测试",
                repository_url="https://github.com/example/test-project",
                branch="main",
                default_test_path="./tests",
                default_pytest_options=["-v", "--tb=short"],
                environment_vars={"ENV": "test", "DEBUG": "true"},
                notification_config={"email": "test@example.com"},
                is_active=True,
            )
            print(f"✓ 项目创建成功: {project.name} (ID: {project.id})")
            
            # 查询项目
            print("查询项目...")
            fetched_project = await get_project_by_name(session, "test-project-1")
            if fetched_project:
                print(f"✓ 项目查询成功: {fetched_project.name}")
            else:
                print("✗ 项目查询失败")
                return False
            
            # 查询项目列表
            print("查询项目列表...")
            projects = await get_projects(session, is_active=True)
            print(f"✓ 找到 {len(projects)} 个活跃项目")
            
            return True
            
    except Exception as e:
        print(f"✗ 项目CRUD操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db.disconnect()


async def test_test_run_crud():
    """测试测试运行CRUD操作"""
    print("\n" + "=" * 60)
    print("4. 测试测试运行CRUD操作")
    print("=" * 60)
    
    db = Database()
    await db.connect()
    
    try:
        async with db.get_session() as session:
            # 获取项目
            project = await get_project_by_name(session, "test-project-1")
            if not project:
                print("✗ 找不到测试项目")
                return False
            
            # 创建测试运行
            print("创建测试运行...")
            test_run = await create_test_run(
                session=session,
                project_id=project.id,
                test_path="./tests/test_example.py",
                pytest_options=["-v", "--tb=short"],
                status=TestRunStatus.RUNNING,
                start_time=datetime.utcnow(),
            )
            print(f"✓ 测试运行创建成功: ID={test_run.id}")
            
            # 更新测试结果
            print("更新测试结果...")
            updated_run = await update_test_run_results(
                session=session,
                run_id=test_run.id,
                total_tests=10,
                passed=8,
                failed=1,
                skipped=1,
                error=0,
                duration=12.5,
                status=TestRunStatus.COMPLETED,
            )
            if updated_run:
                print(f"✓ 测试结果更新成功: 成功率={updated_run.success_rate:.1f}%")
            else:
                print("✗ 测试结果更新失败")
                return False
            
            # 查询测试运行
            print("查询测试运行详情...")
            fetched_run = await get_test_run(session, test_run.id)
            if fetched_run:
                print(f"✓ 测试运行查询成功: {fetched_run.status.value}")
                print(f"  测试统计: 总数={fetched_run.total_tests}, 通过={fetched_run.passed}, "
                      f"失败={fetched_run.failed}, 跳过={fetched_run.skipped}")
            else:
                print("✗ 测试运行查询失败")
                return False
            
            return True
            
    except Exception as e:
        print(f"✗ 测试运行CRUD操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db.disconnect()


async def test_test_case_crud():
    """测试测试用例CRUD操作"""
    print("\n" + "=" * 60)
    print("5. 测试测试用例CRUD操作")
    print("=" * 60)
    
    db = Database()
    await db.connect()
    
    try:
        async with db.get_session() as session:
            # 获取项目
            project = await get_project_by_name(session, "test-project-1")
            if not project:
                print("✗ 找不到测试项目")
                return False
            
            # 获取测试运行
            test_runs = await get_test_runs(session, project_id=project.id, limit=1)
            if not test_runs:
                print("✗ 找不到测试运行")
                return False
            
            test_run = test_runs[0]
            
            # 创建单个测试用例
            print("创建单个测试用例...")
            test_case = await create_test_case(
                session=session,
                run_id=test_run.id,
                test_name="test_example.py::test_addition",
                test_file="test_example.py",
                test_class=None,
                test_method="test_addition",
                status=TestCaseStatus.PASSED,
                duration=0.25,
                error_message=None,
                stack_trace=None,
                stdout="测试通过",
                stderr="",
            )
            print(f"✓ 测试用例创建成功: {test_case.test_name}")
            
            # 批量创建测试用例
            print("批量创建测试用例...")
            test_cases_data = [
                {
                    "run_id": test_run.id,
                    "test_name": "test_example.py::test_subtraction",
                    "status": "passed",
                    "duration": 0.15,
                    "test_file": "test_example.py",
                    "test_method": "test_subtraction",
                },
                {
                    "run_id": test_run.id,
                    "test_name": "test_example.py::test_multiplication",
                    "status": "failed",
                    "duration": 0.35,
                    "test_file": "test_example.py",
                    "test_method": "test_multiplication",
                    "error_message": "AssertionError: 6 != 7",
                    "stack_trace": "Traceback...",
                },
                {
                    "run_id": test_run.id,
                    "test_name": "test_example.py::test_division",
                    "status": "skipped",
                    "duration": 0.0,
                    "test_file": "test_example.py",
                    "test_method": "test_division",
                },
            ]
            
            batch_cases = await create_test_cases_batch(session, test_cases_data)
            print(f"✓ 批量创建 {len(batch_cases)} 个测试用例")
            
            # 查询测试用例
            print("查询测试运行的所有测试用例...")
            test_cases = await get_test_cases_by_run(session, test_run.id)
            print(f"✓ 找到 {len(test_cases)} 个测试用例")
            
            # 统计状态
            status_count = {}
            for case in test_cases:
                status = case.status.value
                status_count[status] = status_count.get(status, 0) + 1
            
            print("测试用例状态统计:")
            for status, count in status_count.items():
                print(f"  {status}: {count}")
            
            return True
            
    except Exception as e:
        print(f"✗ 测试用例CRUD操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db.disconnect()


async def test_html_report_crud():
    """测试HTML报告CRUD操作"""
    print("\n" + "=" * 60)
    print("6. 测试HTML报告CRUD操作")
    print("=" * 60)
    
    db = Database()
    await db.connect()
    
    try:
        async with db.get_session() as session:
            # 获取项目
            project = await get_project_by_name(session, "test-project-1")
            if not project:
                print("✗ 找不到测试项目")
                return False
            
            # 获取测试运行
            test_runs = await get_test_runs(session, project_id=project.id, limit=1)
            if not test_runs:
                print("✗ 找不到测试运行")
                return False
            
            test_run = test_runs[0]
            
            # 创建HTML报告
            print("创建HTML测试报告...")
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>测试报告 - 测试项目1</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }
                    .passed { color: green; }
                    .failed { color: red; }
                    .skipped { color: orange; }
                </style>
            </head>
            <body>
                <h1>测试报告</h1>
                <div class="summary">
                    <h2>测试统计</h2>
                    <p>总测试数: 10</p>
                    <p>通过: <span class="passed">8</span></p>
                    <p>失败: <span class="failed">1</span></p>
                    <p>跳过: <span class="skipped">1</span></p>
                    <p>成功率: 80%</p>
                </div>
            </body>
            </html>
            """
            
            html_report = await create_html_report(
                session=session,
                run_id=test_run.id,
                report_name="pytest-html-report.html",
                report_type="pytest-html",
                file_path="/tmp/pytest-html-report.html",
                content=html_content,
            )
            print(f"✓ HTML报告创建成功: {html_report.report_name} (大小: {html_report.size} 字节)")
            
            # 查询HTML报告
            print("查询测试运行的HTML报告...")
            reports = await get_html_reports_by_run(session, test_run.id)
            print(f"✓ 找到 {len(reports)} 个HTML报告")
            
            for report in reports:
                print(f"  - {report.report_name} ({report.report_type})")
            
            return True
            
    except Exception as e:
        print(f"✗ HTML报告CRUD操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db.disconnect()


async def test_test_analysis_crud():
    """测试测试分析CRUD操作"""
    print("\n" + "=" * 60)
    print("7. 测试测试分析CRUD操作")
    print("=" * 60)
    
    db = Database()
    await db.connect()
    
    try:
        async with db.get_session() as session:
            # 获取项目
            project = await get_project_by_name(session, "test-project-1")
            if not project:
                print("✗ 找不到测试项目")
                return False
            
            # 获取测试运行
            test_runs = await get_test_runs(session, project_id=project.id, limit=1)
            if not test_runs:
                print("✗ 找不到测试运行")
                return False
            
            test_run = test_runs[0]
            
            # 创建性能分析
            print("创建性能分析...")
            performance_analysis = await create_test_analysis(
                session=session,
                run_id=test_run.id,
                analysis_type="performance",
                metrics={
                    "total_duration": 12.5,
                    "avg_test_duration": 1.25,
                    "slowest_test": "test_multiplication",
                    "slowest_duration": 0.35,
                    "fastest_test": "test_subtraction",
                    "fastest_duration": 0.15,
                },
                summary="测试执行性能良好，平均测试时间1.25秒",
                recommendations=[
                    {"type": "optimization", "test": "test_multiplication", "suggestion": "优化算法复杂度"},
                    {"type": "monitoring", "suggestion": "监控长时间运行的测试"},
                ],
            )
            print(f"✓ 性能分析创建成功: {performance_analysis.analysis_type}")
            
            # 创建覆盖率分析
            print("创建覆盖率分析...")
            coverage_analysis = await create_test_analysis(
                session=session,
                run_id=test_run.id,
                analysis_type="coverage",
                metrics={
                    "line_coverage": 85.5,
                    "branch_coverage": 72.3,
                    "function_coverage": 90.1,
                    "total_lines": 1000,
                    "covered_lines": 855,
                },
                summary="代码覆盖率良好，但分支覆盖率有待提高",
                recommendations=[
                    {"type": "coverage", "suggestion": "增加边界条件测试"},
                    {"type": "coverage", "suggestion": "添加异常场景测试"},
                ],
            )
            print(f"✓ 覆盖率分析创建成功: {coverage_analysis.analysis_type}")
            
            # 查询测试分析
            print("查询测试运行的分析结果...")
            analyses = await get_test_analyses_by_run(session, test_run.id)
            print(f"✓ 找到 {len(analyses)} 个分析结果")
            
            for analysis in analyses:
                print(f"  - {analysis.analysis_type}: {analysis.summary[:50]}...")
            
            return True
            
    except Exception as e:
        print(f"✗ 测试分析CRUD操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db.disconnect()


async def test_statistics():
    """测试统计分析功能"""
    print("\n" + "=" * 60)
    print("8. 测试统计分析功能")
    print("=" * 60)
    
    db = Database()
    await db.connect()
    
    try:
        async with db.get_session() as session:
            # 获取项目
            project = await get_project_by_name(session, "test-project-1")
            if not project:
                print("✗ 找不到测试项目")
                return False
            
            # 获取项目统计
            print("获取项目统计信息...")
            stats = await get_project_statistics(session, project.id, days=7)
            print(f"✓ 项目统计获取成功")
            print(f"  总运行次数: {stats['total_runs']}")
            print(f"  总测试用例数: {stats['total_tests']}")
            print(f"  平均成功率: {stats['avg_success_rate']:.1f}%")
            print(f"  平均运行时间: {stats['avg_duration']:.2f}秒")
            print(f"  趋势: {stats['trend']}")
            
            # 获取不稳定测试
            print("\n识别不稳定测试...")
            flaky_tests = await get_flaky_tests(session, project.id, days=7, threshold=0.3)
            print(f"✓ 找到 {len(flaky_tests)} 个不稳定测试")
            
            if flaky_tests:
                print("不稳定测试列表:")
                for i, test in enumerate(flaky_tests[:3], 1):
                    print(f"  {i}. {test['test_name']} (失败率: {test['failed_rate']:.1%})")
            
            return True
            
    except Exception as e:
        print(f"✗ 统计分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db.disconnect()


async def main():
    """主函数"""
    print("=" * 80)
    print("MySQL集成测试")
    print("=" * 80)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("重建表结构", test_recreate_tables),
        ("项目CRUD", test_project_crud),
        ("测试运行CRUD", test_test_run_crud),
        ("测试用例CRUD", test_test_case_crud),
        ("HTML报告CRUD", test_html_report_crud),
        ("测试分析CRUD", test_test_analysis_crud),
        ("统计分析", test_statistics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"✗ 测试 '{test_name}' 异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {len(tests)} 个测试")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)