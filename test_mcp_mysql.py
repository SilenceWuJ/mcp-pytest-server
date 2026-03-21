#!/usr/bin/env python3
"""
测试MCP服务器与MySQL数据库的连接
"""
import asyncio
import subprocess
import time
import requests
import json
import sys
from pathlib import Path

def start_mcp_server():
    """启动MCP服务器"""
    print("启动MCP服务器...")
    
    # 使用虚拟环境中的Python启动服务器
    cmd = ["./venv/bin/python", "simple_server.py"]
    
    # 启动服务器进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(3)
    
    # 检查进程是否在运行
    if process.poll() is not None:
        # 进程已退出，读取错误输出
        stdout, stderr = process.communicate()
        print(f"服务器启动失败:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return None
    
    print("✓ MCP服务器已启动")
    return process

def test_health_check():
    """测试健康检查"""
    print("\n测试健康检查...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ 健康检查通过: {response.json()}")
            return True
        else:
            print(f"✗ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 健康检查异常: {e}")
        return False

def test_mcp_initialize():
    """测试MCP初始化"""
    print("\n测试MCP初始化...")
    
    try:
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                },
                "capabilities": {}
            }
        }
        
        response = requests.post(
            "http://localhost:8000/mcp",
            json=request_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ MCP初始化成功")
            print(f"  服务器: {result.get('result', {}).get('serverInfo', {}).get('name')}")
            print(f"  版本: {result.get('result', {}).get('serverInfo', {}).get('version')}")
            return True
        else:
            print(f"✗ MCP初始化失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ MCP初始化异常: {e}")
        return False

def test_tools_list():
    """测试工具列表"""
    print("\n测试工具列表...")
    
    try:
        request_data = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = requests.post(
            "http://localhost:8000/mcp",
            json=request_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            tools = result.get('result', {}).get('tools', [])
            print(f"✓ 找到 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  • {tool.get('name')}: {tool.get('description')}")
            return True
        else:
            print(f"✗ 工具列表失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 工具列表异常: {e}")
        return False

def test_run_pytest():
    """测试运行pytest"""
    print("\n测试运行pytest...")
    
    try:
        request_data = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "run_pytest_tests",
                "arguments": {
                    "test_path": "tests/test_example.py",
                    "project_name": "mysql-test",
                    "pytest_options": ["-v", "--tb=short"],
                    "store_to_db": True
                }
            }
        }
        
        response = requests.post(
            "http://localhost:8000/mcp",
            json=request_data,
            timeout=30  # 给测试更多时间
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'error' in result:
                print(f"✗ 工具调用错误: {result['error']}")
                return False
            else:
                print(f"✓ pytest测试执行完成")
                
                # 解析结果
                result_data = result.get('result', {})
                content = result_data.get('content', [])
                
                for item in content:
                    if item.get('type') == 'text':
                        print(f"  结果: {item.get('text', '')[:100]}...")
                
                return True
        else:
            print(f"✗ pytest测试失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ pytest测试异常: {e}")
        return False

def test_http_execute():
    """测试HTTP执行接口"""
    print("\n测试HTTP执行接口...")
    
    try:
        request_data = {
            "test_path": "tests/test_example.py",
            "project_name": "http-mysql-test",
            "pytest_options": ["-v"]
        }
        
        response = requests.post(
            "http://localhost:8000/execute",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ HTTP执行接口成功")
            print(f"  状态: {result.get('result', {}).get('isError', 'unknown')}")
            return True
        else:
            print(f"✗ HTTP执行接口失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ HTTP执行接口异常: {e}")
        return False

def check_mysql_test_results():
    """检查MySQL中的测试结果"""
    print("\n检查MySQL中的测试结果...")
    
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    
    async def check_results():
        mysql_url = "mysql+aiomysql://qa_user:123456@localhost:3306/qa_platform"
        
        engine = create_async_engine(
            mysql_url,
            echo=False,
            pool_pre_ping=True,
        )
        
        try:
            async with engine.connect() as conn:
                # 检查test_runs表
                result = await conn.execute(text("SELECT COUNT(*) FROM test_runs"))
                total_runs = result.scalar()
                print(f"  test_runs表总记录数: {total_runs}")
                
                if total_runs > 0:
                    result = await conn.execute(text("""
                        SELECT id, project_name, test_path, status, total_tests, passed, failed, created_at
                        FROM test_runs 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """))
                    runs = result.fetchall()
                    
                    print(f"  最近5条测试记录:")
                    for run in runs:
                        run_id, project, test_path, status, total, passed, failed, created_at = run
                        print(f"    - ID: {run_id}, 项目: {project}, 状态: {status}, 结果: {passed}/{total}通过, 时间: {created_at}")
                
                # 检查test_cases表
                result = await conn.execute(text("SELECT COUNT(*) FROM test_cases"))
                total_cases = result.scalar()
                print(f"  test_cases表总记录数: {total_cases}")
                
                if total_cases > 0 and total_runs > 0:
                    # 获取最新的run_id
                    result = await conn.execute(text("SELECT id FROM test_runs ORDER BY created_at DESC LIMIT 1"))
                    latest_run_id = result.scalar()
                    
                    result = await conn.execute(text("""
                        SELECT COUNT(*) FROM test_cases WHERE run_id = :run_id
                    """), {"run_id": latest_run_id})
                    cases_count = result.scalar()
                    
                    print(f"  最新测试运行({latest_run_id})的用例数: {cases_count}")
                    
                    result = await conn.execute(text("""
                        SELECT test_name, status, duration, error_message
                        FROM test_cases 
                        WHERE run_id = :run_id
                        ORDER BY id
                    """), {"run_id": latest_run_id})
                    cases = result.fetchall()
                    
                    for case in cases[:3]:  # 只显示前3个
                        test_name, status, duration, error = case
                        print(f"    - {test_name}: {status} ({duration:.2f}s)")
                        if error:
                            print(f"      错误: {error[:50]}...")
                
                await conn.close()
            
            return total_runs > 0
            
        except Exception as e:
            print(f"  检查MySQL失败: {e}")
            return False
        finally:
            await engine.dispose()
    
    # 运行异步检查
    return asyncio.run(check_results())

def main():
    """主函数"""
    print("=" * 60)
    print("MCP服务器与MySQL集成测试")
    print("=" * 60)
    
    server_process = None
    tests_passed = 0
    total_tests = 0
    
    try:
        # 启动服务器
        server_process = start_mcp_server()
        if not server_process:
            print("无法启动服务器，测试终止")
            return
        
        # 等待服务器完全启动
        time.sleep(2)
        
        # 运行测试
        tests = [
            ("健康检查", test_health_check),
            ("MCP初始化", test_mcp_initialize),
            ("工具列表", test_tools_list),
            ("运行pytest", test_run_pytest),
            ("HTTP执行", test_http_execute),
        ]
        
        for test_name, test_func in tests:
            total_tests += 1
            if test_func():
                tests_passed += 1
        
        # 检查MySQL中的结果
        print("\n" + "=" * 60)
        print("数据库结果验证")
        print("=" * 60)
        
        if check_mysql_test_results():
            print("✓ 测试结果已成功保存到MySQL数据库")
            tests_passed += 1
        total_tests += 1
        
        # 总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {tests_passed}")
        print(f"失败: {total_tests - tests_passed}")
        
        if tests_passed == total_tests:
            print("\n✅ 所有测试通过!")
        else:
            print(f"\n⚠ {total_tests - tests_passed} 个测试失败")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 停止服务器
        if server_process:
            print("\n停止MCP服务器...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                print("✓ 服务器已停止")
            except subprocess.TimeoutExpired:
                print("⚠ 服务器终止超时，强制结束")
                server_process.kill()
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)

if __name__ == "__main__":
    main()