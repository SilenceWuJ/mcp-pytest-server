#!/usr/bin/env python3
"""
添加测试用例、执行记录、报告等信息到数据库表中
报告信息以file-path形式存储
"""
import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, insert, select, update

# 数据库连接配置
DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/qa_platform"

async def add_test_data():
    """添加测试数据到数据库"""
    print("开始添加测试数据...")
    
    # 创建异步引擎
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # 1. 首先检查并添加项目
            print("1. 添加项目数据...")
            
            # 检查项目是否存在
            result = await session.execute(
                text("SELECT id, name FROM projects WHERE name = 'QA测试平台'")
            )
            project = result.fetchone()
            
            if project:
                project_id = project[0]
                print(f"   项目已存在: {project[1]} (ID: {project_id})")
            else:
                # 添加新项目
                await session.execute(
                    text("""
                    INSERT INTO projects (name, start_date, end_date, progress, created_at) 
                    VALUES ('QA测试平台', '2024-01-01', '2024-12-31', 75, NOW())
                    """)
                )
                await session.commit()
                
                # 获取新插入的项目ID
                result = await session.execute(
                    text("SELECT LAST_INSERT_ID()")
                )
                project_id = result.scalar()
                print(f"   添加新项目: QA测试平台 (ID: {project_id})")
            
            # 2. 添加测试用例
            print("\n2. 添加测试用例数据...")
            
            test_cases = [
                {
                    'name': '用户登录功能测试',
                    'description': '测试用户登录功能是否正常',
                    'steps': '1. 打开登录页面\n2. 输入用户名和密码\n3. 点击登录按钮',
                    'expected_result': '登录成功，跳转到首页',
                    'project_id': project_id,
                    'requirement_id': None,
                    'test_phase_id': 1,
                    'test_type_id': 1,
                    'mark_id': 1,
                    'test_script': 'def test_user_login():\n    # 测试代码...'
                },
                {
                    'name': '用户注册功能测试',
                    'description': '测试用户注册功能是否正常',
                    'steps': '1. 打开注册页面\n2. 填写注册信息\n3. 点击注册按钮',
                    'expected_result': '注册成功，发送验证邮件',
                    'project_id': project_id,
                    'requirement_id': None,
                    'test_phase_id': 1,
                    'test_type_id': 1,
                    'mark_id': 1,
                    'test_script': 'def test_user_register():\n    # 测试代码...'
                },
                {
                    'name': '商品搜索功能测试',
                    'description': '测试商品搜索功能是否正常',
                    'steps': '1. 在搜索框输入关键词\n2. 点击搜索按钮\n3. 查看搜索结果',
                    'expected_result': '显示相关商品列表',
                    'project_id': project_id,
                    'requirement_id': None,
                    'test_phase_id': 2,
                    'test_type_id': 2,
                    'mark_id': 2,
                    'test_script': 'def test_product_search():\n    # 测试代码...'
                },
                {
                    'name': '购物车功能测试',
                    'description': '测试购物车添加商品功能',
                    'steps': '1. 浏览商品\n2. 点击加入购物车\n3. 查看购物车',
                    'expected_result': '商品成功添加到购物车',
                    'project_id': project_id,
                    'requirement_id': None,
                    'test_phase_id': 2,
                    'test_type_id': 2,
                    'mark_id': 2,
                    'test_script': 'def test_shopping_cart():\n    # 测试代码...'
                },
                {
                    'name': '支付功能测试',
                    'description': '测试支付流程是否正常',
                    'steps': '1. 选择支付方式\n2. 输入支付信息\n3. 确认支付',
                    'expected_result': '支付成功，生成订单',
                    'project_id': project_id,
                    'requirement_id': None,
                    'test_phase_id': 3,
                    'test_type_id': 3,
                    'mark_id': 3,
                    'test_script': 'def test_payment():\n    # 测试代码...'
                }
            ]
            
            testcase_ids = []
            for i, test_case in enumerate(test_cases, 1):
                # 检查测试用例是否存在
                result = await session.execute(
                    text("SELECT id FROM testcases WHERE name = :name AND project_id = :project_id"),
                    {'name': test_case['name'], 'project_id': project_id}
                )
                existing = result.fetchone()
                
                if existing:
                    testcase_id = existing[0]
                    print(f"   测试用例已存在: {test_case['name']} (ID: {testcase_id})")
                else:
                    # 添加新测试用例
                    await session.execute(
                        text("""
                        INSERT INTO testcases (
                            name, description, steps, expected_result, project_id,
                            requirement_id, test_phase_id, test_type_id, mark_id,
                            test_script, created_at, updated_at
                        ) VALUES (
                            :name, :description, :steps, :expected_result, :project_id,
                            :requirement_id, :test_phase_id, :test_type_id, :mark_id,
                            :test_script, NOW(), NOW()
                        )
                        """),
                        test_case
                    )
                    await session.commit()
                    
                    # 获取新插入的测试用例ID
                    result = await session.execute(
                        text("SELECT LAST_INSERT_ID()")
                    )
                    testcase_id = result.scalar()
                    print(f"   添加测试用例 {i}: {test_case['name']} (ID: {testcase_id})")
                
                testcase_ids.append(testcase_id)
            
            # 3. 添加测试执行记录
            print("\n3. 添加测试执行记录...")
            
            test_runs = [
                {
                    'project_name': 'QA测试平台',
                    'test_path': '/tests/test_login.py',
                    'total_tests': 10,
                    'passed': 8,
                    'failed': 1,
                    'skipped': 1,
                    'duration': 45.2,
                    'status': 'completed',
                    'created_at': datetime.now() - timedelta(days=2)
                },
                {
                    'project_name': 'QA测试平台',
                    'test_path': '/tests/test_registration.py',
                    'total_tests': 15,
                    'passed': 14,
                    'failed': 0,
                    'skipped': 1,
                    'duration': 62.8,
                    'status': 'completed',
                    'created_at': datetime.now() - timedelta(days=1)
                },
                {
                    'project_name': 'QA测试平台',
                    'test_path': '/tests/test_ecommerce.py',
                    'total_tests': 25,
                    'passed': 23,
                    'failed': 2,
                    'skipped': 0,
                    'duration': 120.5,
                    'status': 'completed',
                    'created_at': datetime.now()
                }
            ]
            
            run_ids = []
            for i, test_run in enumerate(test_runs, 1):
                # 添加测试执行记录
                await session.execute(
                    text("""
                    INSERT INTO mcp_test_runs (
                        project_name, test_path, total_tests, passed, failed,
                        skipped, duration, status, created_at
                    ) VALUES (
                        :project_name, :test_path, :total_tests, :passed, :failed,
                        :skipped, :duration, :status, :created_at
                    )
                    """),
                    test_run
                )
                await session.commit()
                
                # 获取新插入的执行记录ID
                result = await session.execute(
                    text("SELECT LAST_INSERT_ID()")
                )
                run_id = result.scalar()
                run_ids.append(run_id)
                print(f"   添加测试执行记录 {i}: {test_run['test_path']} (ID: {run_id})")
            
            # 4. 添加测试报告（以file-path形式存储）
            print("\n4. 添加测试报告（file-path形式）...")
            
            test_reports = [
                {
                    'testcase_id': testcase_ids[0],
                    'status': 'passed',
                    'result': '测试通过，所有功能正常',
                    'started_at': datetime.now() - timedelta(hours=2),
                    'finished_at': datetime.now() - timedelta(hours=1, minutes=50),
                    'log': '测试日志：用户登录功能测试完成'
                },
                {
                    'testcase_id': testcase_ids[1],
                    'status': 'passed',
                    'result': '测试通过，注册流程正常',
                    'started_at': datetime.now() - timedelta(hours=3),
                    'finished_at': datetime.now() - timedelta(hours=2, minutes=30),
                    'log': '测试日志：用户注册功能测试完成'
                },
                {
                    'testcase_id': testcase_ids[2],
                    'status': 'failed',
                    'result': '测试失败，搜索功能有bug',
                    'started_at': datetime.now() - timedelta(hours=4),
                    'finished_at': datetime.now() - timedelta(hours=3, minutes=45),
                    'log': '测试日志：商品搜索功能测试失败，需要修复'
                },
                {
                    'testcase_id': testcase_ids[3],
                    'status': 'passed',
                    'result': '测试通过，购物车功能正常',
                    'started_at': datetime.now() - timedelta(hours=5),
                    'finished_at': datetime.now() - timedelta(hours=4, minutes=20),
                    'log': '测试日志：购物车功能测试完成'
                },
                {
                    'testcase_id': testcase_ids[4],
                    'status': 'passed',
                    'result': '测试通过，支付流程正常',
                    'started_at': datetime.now() - timedelta(hours=6),
                    'finished_at': datetime.now() - timedelta(hours=5, minutes=10),
                    'log': '测试日志：支付功能测试完成'
                }
            ]
            
            for i, report in enumerate(test_reports, 1):
                # 添加测试报告
                await session.execute(
                    text("""
                    INSERT INTO test_reports (
                        testcase_id, status, result, started_at, finished_at, log
                    ) VALUES (
                        :testcase_id, :status, :result, :started_at, :finished_at, :log
                    )
                    """),
                    report
                )
                await session.commit()
                
                print(f"   添加测试报告 {i}: 测试用例ID={report['testcase_id']}, 状态={report['status']}")
            
            # 5. 添加HTML报告文件路径
            print("\n5. 添加HTML报告文件路径...")
            
            html_reports = [
                {
                    'execution_id': run_ids[0],
                    'content': 'HTML报告内容：登录功能测试报告',
                    'html_content': '<html><body><h1>登录功能测试报告</h1></body></html>',
                    'created_at': datetime.now() - timedelta(days=2)
                },
                {
                    'execution_id': run_ids[1],
                    'content': 'HTML报告内容：注册功能测试报告',
                    'html_content': '<html><body><h1>注册功能测试报告</h1></body></html>',
                    'created_at': datetime.now() - timedelta(days=1)
                },
                {
                    'execution_id': run_ids[2],
                    'content': 'HTML报告内容：电商功能测试报告',
                    'html_content': '<html><body><h1>电商功能测试报告</h1></body></html>',
                    'created_at': datetime.now()
                }
            ]
            
            for i, report in enumerate(html_reports, 1):
                # 添加HTML报告
                await session.execute(
                    text("""
                    INSERT INTO reports (
                        execution_id, content, html_content, created_at
                    ) VALUES (
                        :execution_id, :content, :html_content, :created_at
                    )
                    """),
                    report
                )
                await session.commit()
                
                print(f"   添加HTML报告 {i}: 执行ID={report['execution_id']}")
            
            # 6. 添加文件记录（用于存储报告文件路径）
            print("\n6. 添加文件记录（报告文件路径）...")
            
            files = [
                {
                    'filename': 'login_test_report.html',
                    'original_filename': 'login_test_report.html',
                    'file_path': '/reports/2024/03/24/login_test_report.html',
                    'file_size': 10240,
                    'mime_type': 'text/html',
                    'uploaded_at': datetime.now() - timedelta(days=2),
                    'uploader_id': 1
                },
                {
                    'filename': 'registration_test_report.html',
                    'original_filename': 'registration_test_report.html',
                    'file_path': '/reports/2024/03/25/registration_test_report.html',
                    'file_size': 15360,
                    'mime_type': 'text/html',
                    'uploaded_at': datetime.now() - timedelta(days=1),
                    'uploader_id': 1
                },
                {
                    'filename': 'ecommerce_test_report.html',
                    'original_filename': 'ecommerce_test_report.html',
                    'file_path': '/reports/2024/03/26/ecommerce_test_report.html',
                    'file_size': 20480,
                    'mime_type': 'text/html',
                    'uploaded_at': datetime.now(),
                    'uploader_id': 1
                }
            ]
            
            file_ids = []
            for i, file in enumerate(files, 1):
                # 检查文件是否已存在
                result = await session.execute(
                    text("SELECT id FROM files WHERE file_path = :file_path"),
                    {'file_path': file['file_path']}
                )
                existing = result.fetchone()
                
                if existing:
                    file_id = existing[0]
                    print(f"   文件已存在: {file['filename']} (ID: {file_id})")
                else:
                    # 添加文件记录
                    await session.execute(
                        text("""
                        INSERT INTO files (
                            filename, original_filename, file_path, file_size,
                            mime_type, uploaded_at, uploader_id
                        ) VALUES (
                            :filename, :original_filename, :file_path, :file_size,
                            :mime_type, :uploaded_at, :uploader_id
                        )
                        """),
                        file
                    )
                    await session.commit()
                    
                    # 获取新插入的文件ID
                    result = await session.execute(
                        text("SELECT LAST_INSERT_ID()")
                    )
                    file_id = result.scalar()
                    print(f"   添加文件记录 {i}: {file['filename']} (路径: {file['file_path']}, ID: {file_id})")
                
                file_ids.append(file_id)
            
            # 7. 关联测试用例和文件
            print("\n7. 关联测试用例和报告文件...")
            
            # 关联前5个测试用例和文件
            for i, testcase_id in enumerate(testcase_ids[:3]):
                file_id = file_ids[i % len(file_ids)]
                
                # 检查关联是否已存在
                result = await session.execute(
                    text("""
                    SELECT * FROM testcase_files 
                    WHERE testcase_id = :testcase_id AND file_id = :file_id
                    """),
                    {'testcase_id': testcase_id, 'file_id': file_id}
                )
                existing = result.fetchone()
                
                if not existing:
                    await session.execute(
                        text("""
                        INSERT INTO testcase_files (testcase_id, file_id)
                        VALUES (:testcase_id, :file_id)
                        """),
                        {'testcase_id': testcase_id, 'file_id': file_id}
                    )
                    await session.commit()
                    print(f"   关联测试用例ID={testcase_id} 和文件ID={file_id}")
            
            await session.commit()
            print("\n✅ 测试数据添加完成！")
            
            # 显示统计信息
            print("\n📊 数据统计:")
            print(f"   项目数量: 1 (QA测试平台)")
            print(f"   测试用例数量: {len(testcase_ids)}")
            print(f"   测试执行记录: {len(run_ids)}")
            print(f"   测试报告数量: {len(test_reports)}")
            print(f"   HTML报告数量: {len(html_reports)}")
            print(f"   文件记录数量: {len(file_ids)}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 添加数据时出错: {e}")
            raise
        finally:
            await session.close()
    
    await engine.dispose()

async def verify_data():
    """验证添加的数据"""
    print("\n🔍 验证数据库中的数据...")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # 统计各表数据量
            tables = ['projects', 'testcases', 'mcp_test_runs', 'test_reports', 'reports', 'files', 'testcase_files']
            
            for table in tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   {table}: {count} 条记录")
            
            # 显示最近添加的测试用例
            print("\n📋 最近添加的测试用例:")
            result = await session.execute(
                text("SELECT id, name, description FROM testcases ORDER BY created_at DESC LIMIT 3")
            )
            testcases = result.fetchall()
            
            for tc in testcases:
                print(f"   ID: {tc[0]}, 名称: {tc[1]}")
                print(f"       描述: {tc[2][:50]}..." if tc[2] and len(tc[2]) > 50 else f"       描述: {tc[2]}")
            
            # 显示测试执行记录
            print("\n📈 测试执行记录:")
            result = await session.execute(
                text("""
                SELECT id, project_name, test_path, total_tests, passed, failed, status 
                FROM mcp_test_runs ORDER BY created_at DESC LIMIT 3
                """)
            )
            runs = result.fetchall()
            
            for run in runs:
                success_rate = (run[3] / run[3] * 100) if run[3] > 0 else 0
                print(f"   ID: {run[0]}, 项目: {run[1]}")
                print(f"       测试路径: {run[2]}")
                print(f"       结果: {run[4]}/{run[3]} 通过, {run[5]} 失败, 状态: {run[6]}")
            
            # 显示报告文件路径
            print("\n📁 报告文件路径:")
            result = await session.execute(
                text("SELECT id, filename, file_path, file_size FROM files ORDER BY uploaded_at DESC LIMIT 3")
            )
            files = result.fetchall()
            
            for file in files:
                size_kb = file[3] / 1024
                print(f"   ID: {file[0]}, 文件名: {file[1]}")
                print(f"       文件路径: {file[2]}")
                print(f"       文件大小: {size_kb:.1f} KB")
            
        except Exception as e:
            print(f"❌ 验证数据时出错: {e}")
        finally:
            await session.close()
    
    await engine.dispose()

async def main():
    """主函数"""
    print("=" * 60)
    print("添加测试数据到数据库")
    print("=" * 60)
    
    try:
        # 添加测试数据
        await add_test_data()
        
        # 验证数据
        await verify_data()
        
        print("\n" + "=" * 60)
        print("✅ 任务完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())