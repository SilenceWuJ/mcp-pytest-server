#!/usr/bin/env python3
"""
简单的MCP服务器测试脚本
"""
import asyncio
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_database():
    """测试数据库功能"""
    print("测试数据库功能...")
    try:
        from database.connection import Database
        from database.models import Base
        
        db = Database("sqlite:///./test_simple.db")
        await db.connect()
        
        # 创建表
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✓ 数据库连接和表创建成功")
        
        await db.disconnect()
        return True
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False

async def test_pytest_executor():
    """测试pytest执行器"""
    print("\n测试pytest执行器...")
    try:
        from pytest_executor.models import TestResult, TestCaseResult, TestStatus
        from pytest_executor.runner import run_pytest_tests
        from pytest_executor.models import PytestConfig, ExecutionContext
        
        # 创建测试结果对象
        result = TestResult(
            project_name="test_project",
            test_path="tests/test_example.py",
            total_tests=5,
            passed=4,
            failed=1,
            duration=1.23,
            status="completed"
        )
        
        print(f"✓ 测试结果对象创建成功:")
        print(f"  项目: {result.project_name}")
        print(f"  测试路径: {result.test_path}")
        print(f"  总测试数: {result.total_tests}")
        print(f"  通过: {result.passed}")
        print(f"  失败: {result.failed}")
        print(f"  成功率: {result.success_rate:.1f}%")
        
        return True
    except Exception as e:
        print(f"✗ pytest执行器测试失败: {e}")
        return False

async def test_mcp_models():
    """测试MCP模型"""
    print("\n测试MCP模型...")
    try:
        from mcp.models import (
            MCPServerInfo,
            MCPTool,
            MCPRequest,
            MCPResponse
        )
        
        # 创建服务器信息
        server_info = MCPServerInfo(
            name="test-server",
            version="1.0.0",
            capabilities={"tools": {}, "resources": {}}
        )
        
        # 创建工具定义
        tool = MCPTool(
            name="test_tool",
            description="测试工具",
            inputSchema={"type": "object", "properties": {}}
        )
        
        # 创建请求
        request = MCPRequest(
            id=1,
            method="tools/list",
            params={}
        )
        
        # 创建响应
        response = MCPResponse(
            id=1,
            result={"tools": [tool.dict()]}
        )
        
        print("✓ MCP模型创建成功:")
        print(f"  服务器: {server_info.name} v{server_info.version}")
        print(f"  工具: {tool.name} - {tool.description}")
        
        return True
    except Exception as e:
        print(f"✗ MCP模型测试失败: {e}")
        return False

async def test_config():
    """测试配置系统"""
    print("\n测试配置系统...")
    try:
        from config import settings
        
        print("✓ 配置系统加载成功:")
        print(f"  服务器: {settings.host}:{settings.port}")
        print(f"  数据库: {settings.database_url}")
        print(f"  调试模式: {settings.debug}")
        print(f"  服务器名称: {settings.mcp_server_name}")
        
        return True
    except Exception as e:
        print(f"✗ 配置系统测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("MCP Pytest服务器功能测试")
    print("=" * 60)
    
    tests = [
        test_config,
        test_database,
        test_pytest_executor,
        test_mcp_models,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    for i, (test_func, result) in enumerate(zip(tests, results), 1):
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{i}. {test_func.__name__}: {status}")
    
    total_passed = sum(results)
    total_tests = len(results)
    
    print(f"\n总计: {total_passed}/{total_tests} 通过 ({total_passed/total_tests*100:.0f}%)")
    
    if total_passed == total_tests:
        print("\n🎉 所有测试通过！服务器核心功能正常。")
        return 0
    else:
        print("\n⚠ 部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)