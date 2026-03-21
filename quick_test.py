#!/usr/bin/env python3
"""
快速测试MCP服务器
"""
import sys
import os

# 测试1: 检查Python版本
print("=" * 60)
print("测试1: Python环境检查")
print("=" * 60)
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")

# 测试2: 检查依赖
print("\n" + "=" * 60)
print("测试2: 依赖检查")
print("=" * 60)

try:
    import fastapi
    print(f"✓ FastAPI: {fastapi.__version__}")
except ImportError:
    print("✗ FastAPI: 未安装")

try:
    import pydantic
    print(f"✓ Pydantic: {pydantic.__version__}")
except ImportError:
    print("✗ Pydantic: 未安装")

try:
    import sqlalchemy
    print(f"✓ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError:
    print("✗ SQLAlchemy: 未安装")

try:
    import pytest
    print(f"✓ Pytest: {pytest.__version__}")
except ImportError:
    print("✗ Pytest: 未安装")

# 测试3: 检查项目结构
print("\n" + "=" * 60)
print("测试3: 项目结构检查")
print("=" * 60)

required_files = [
    "src/main.py",
    "src/config.py",
    "src/database/__init__.py",
    "src/pytest_executor/__init__.py",
    "src/mcp/__init__.py",
    "requirements_fixed.txt",
    "tests/test_example.py",
]

all_files_exist = True
for file_path in required_files:
    if os.path.exists(file_path):
        print(f"✓ {file_path}")
    else:
        print(f"✗ {file_path} (缺失)")
        all_files_exist = False

# 测试4: 尝试导入主要模块
print("\n" + "=" * 60)
print("测试4: 模块导入检查")
print("=" * 60)

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import config
    print("✓ config 模块导入成功")
except Exception as e:
    print(f"✗ config 模块导入失败: {e}")

try:
    # 测试数据库模型
    from database.models import Base, TestRun, TestCase
    print("✓ database.models 导入成功")
except Exception as e:
    print(f"✗ database.models 导入失败: {e}")

try:
    # 测试pytest执行器模型
    from pytest_executor.models import TestResult, TestCaseResult
    print("✓ pytest_executor.models 导入成功")
except Exception as e:
    print(f"✗ pytest_executor.models 导入失败: {e}")

try:
    # 测试MCP模型
    from mcp.models import MCPServerInfo, MCPTool
    print("✓ mcp.models 导入成功")
except Exception as e:
    print(f"✗ mcp.models 导入失败: {e}")

# 测试5: 创建示例数据
print("\n" + "=" * 60)
print("测试5: 创建示例数据")
print("=" * 60)

try:
    from pytest_executor.models import TestResult, TestCaseResult, TestStatus
    
    # 创建测试结果
    test_result = TestResult(
        project_name="demo_project",
        test_path="tests/test_example.py",
        total_tests=10,
        passed=8,
        failed=1,
        skipped=1,
        duration=5.67,
        status="completed"
    )
    
    print(f"✓ 创建测试结果:")
    print(f"  项目: {test_result.project_name}")
    print(f"  测试路径: {test_result.test_path}")
    print(f"  总测试数: {test_result.total_tests}")
    print(f"  通过: {test_result.passed}")
    print(f"  失败: {test_result.failed}")
    print(f"  跳过: {test_result.skipped}")
    print(f"  成功率: {test_result.success_rate:.1f}%")
    print(f"  耗时: {test_result.duration:.2f}秒")
    
except Exception as e:
    print(f"✗ 创建示例数据失败: {e}")

# 测试6: 检查启动脚本
print("\n" + "=" * 60)
print("测试6: 启动脚本检查")
print("=" * 60)

if os.path.exists("start.sh"):
    print("✓ start.sh 存在")
    # 检查执行权限
    import stat
    st = os.stat("start.sh")
    if st.st_mode & stat.S_IEXEC:
        print("✓ start.sh 有执行权限")
    else:
        print("⚠ start.sh 没有执行权限，运行: chmod +x start.sh")
else:
    print("✗ start.sh 不存在")

# 总结
print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)

print("\n下一步:")
print("1. 启动服务器: python -m src.main")
print("2. 测试HTTP接口: curl http://localhost:8000/health")
print("3. 执行测试: curl -X POST http://localhost:8000/execute -H 'Content-Type: application/json' -d '{\"test_path\":\"tests/test_example.py\"}'")
print("\nGoose集成:")
print("在Goose配置中添加:")
print("""
mcp_servers:
  pytest_test_server:
    command: "python"
    args: ["-m", "src.main"]
    env:
      MCP_PYTEST_DATABASE_URL: "sqlite:///./test_results.db"
""")