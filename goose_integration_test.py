#!/usr/bin/env python3
"""
Goose集成测试脚本
这个脚本演示如何将MCP服务器集成到Goose中
"""
import json
import subprocess
import time
import sys
import os

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def test_mcp_server():
    """测试MCP服务器"""
    print_header("步骤1: 启动MCP服务器")
    
    # 启动服务器
    server_process = subprocess.Popen(
        [sys.executable, "simple_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("✓ MCP服务器已启动 (PID: {})".format(server_process.pid))
    
    # 等待服务器启动
    time.sleep(2)
    
    # 测试健康检查
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ 服务器健康检查通过")
        else:
            print("✗ 服务器健康检查失败")
            return False
    except Exception as e:
        print(f"✗ 服务器连接失败: {e}")
        return False
    
    return server_process

def test_mcp_protocol():
    """测试MCP协议"""
    print_header("步骤2: 测试MCP协议")
    
    import requests
    
    # 测试初始化
    print("测试MCP初始化...")
    init_response = requests.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "goose-test"},
                "capabilities": {}
            }
        }
    )
    
    if init_response.status_code == 200:
        print("✓ MCP初始化成功")
    else:
        print("✗ MCP初始化失败")
        return False
    
    # 测试工具列表
    print("\n测试工具列表...")
    tools_response = requests.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
    )
    
    if tools_response.status_code == 200:
        data = tools_response.json()
        tools = data.get("result", {}).get("tools", [])
        print(f"✓ 找到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  • {tool['name']}: {tool['description']}")
    else:
        print("✗ 获取工具列表失败")
        return False
    
    # 测试工具调用
    print("\n测试工具调用...")
    call_response = requests.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "run_pytest_tests",
                "arguments": {
                    "test_path": "tests/test_example.py",
                    "project_name": "goose-demo"
                }
            }
        }
    )
    
    if call_response.status_code == 200:
        data = call_response.json()
        result = data.get("result", {})
        if result.get("isError"):
            print("⚠ 测试执行失败（预期中，因为有一个测试设计为失败）")
        else:
            print("✓ 测试执行成功")
        
        # 显示结果
        content = result.get("content", [])
        if content:
            print("\n测试结果:")
            for item in content:
                if item.get("type") == "text":
                    print(item.get("text"))
    else:
        print("✗ 工具调用失败")
        return False
    
    return True

def create_goose_config():
    """创建Goose配置文件"""
    print_header("步骤3: 创建Goose配置文件")
    
    config = {
        "mcp_servers": {
            "pytest_test_server": {
                "command": sys.executable,
                "args": ["simple_server.py"],
                "env": {
                    "PYTHONPATH": os.path.dirname(os.path.abspath(__file__))
                }
            }
        }
    }
    
    config_file = "goose_test_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Goose配置文件已创建: {config_file}")
    print("\n配置文件内容:")
    print(json.dumps(config, indent=2))
    
    return config_file

def create_goose_commands():
    """创建Goose命令示例"""
    print_header("步骤4: Goose命令示例")
    
    commands = [
        {
            "description": "执行pytest测试",
            "goose_command": "请执行pytest测试",
            "expected_mcp_call": {
                "method": "tools/call",
                "params": {
                    "name": "run_pytest_tests",
                    "arguments": {
                        "test_path": "tests/",
                        "project_name": "用户项目"
                    }
                }
            }
        },
        {
            "description": "查看测试历史",
            "goose_command": "显示最近的测试结果",
            "expected_mcp_call": {
                "method": "tools/call",
                "params": {
                    "name": "get_test_history",
                    "arguments": {
                        "limit": 10
                    }
                }
            }
        },
        {
            "description": "运行特定测试文件",
            "goose_command": "运行tests/test_api.py的测试",
            "expected_mcp_call": {
                "method": "tools/call",
                "params": {
                    "name": "run_pytest_tests",
                    "arguments": {
                        "test_path": "tests/test_api.py",
                        "project_name": "用户项目"
                    }
                }
            }
        }
    ]
    
    print("用户可以通过以下方式与Goose交互:\n")
    for i, cmd in enumerate(commands, 1):
        print(f"{i}. {cmd['description']}")
        print(f"   用户说: \"{cmd['goose_command']}\"")
        print(f"   Goose会调用: {cmd['expected_mcp_call']['params']['name']}")
        print()
    
    return commands

def test_http_interface():
    """测试HTTP接口"""
    print_header("步骤5: 测试HTTP接口")
    
    import requests
    
    # 测试执行接口
    print("测试执行接口...")
    execute_response = requests.post(
        "http://localhost:8000/execute",
        json={
            "test_path": "tests/test_example.py",
            "project_name": "http-test"
        }
    )
    
    if execute_response.status_code == 200:
        result = execute_response.json()
        print("✓ HTTP执行接口成功")
        print(f"  状态: {'成功' if result.get('success') else '失败'}")
        print(f"  总测试数: {result.get('result', {}).get('total_tests', 0)}")
        print(f"  通过: {result.get('result', {}).get('passed', 0)}")
        print(f"  失败: {result.get('result', {}).get('failed', 0)}")
    else:
        print("✗ HTTP执行接口失败")
        return False
    
    return True

def create_integration_guide():
    """创建集成指南"""
    print_header("步骤6: Goose集成指南")
    
    guide = """
如何将MCP Pytest服务器集成到Goose中:

1. 配置Goose使用MCP服务器:

   在Goose配置文件 (~/.goose/config.yaml 或项目中的 .goose/config.yaml) 中添加:

   ```yaml
   mcp_servers:
     pytest_test_server:
       command: "python"
       args: 
         - "simple_server.py"
       env:
         PYTHONPATH: "/path/to/mcp-pytest-server"
   ```

2. 或者使用环境变量:

   ```bash
   export GOOSE_MCP_SERVERS='{
     "pytest_test_server": {
       "command": "python",
       "args": ["simple_server.py"],
       "env": {
         "PYTHONPATH": "/path/to/mcp-pytest-server"
       }
     }
   }'
   ```

3. 启动Goose:

   ```bash
   goose
   ```

4. 在Goose中使用测试功能:

   用户可以说:
   - "执行pytest测试"
   - "运行tests/目录下的测试"
   - "查看测试历史"
   - "显示最近的测试结果"

5. Goose会自动:
   - 连接到MCP服务器
   - 发现可用的工具
   - 将用户请求转换为工具调用
   - 显示测试结果

6. 高级用法:
   - 指定测试路径: "运行tests/test_api.py的测试"
   - 指定项目名称: "为my-project项目运行测试"
   - 查看详细结果: "显示测试运行123的详情"
   - 获取统计信息: "显示项目测试统计"
   """
    
    print(guide)
    
    return guide

def main():
    """主函数"""
    print_header("Goose MCP集成测试")
    print("这个脚本演示如何将MCP Pytest服务器集成到Goose中")
    
    try:
        # 步骤1: 启动服务器
        server_process = test_mcp_server()
        if not server_process:
            return 1
        
        try:
            # 步骤2: 测试MCP协议
            if not test_mcp_protocol():
                return 1
            
            # 步骤3: 创建Goose配置
            config_file = create_goose_config()
            
            # 步骤4: 创建命令示例
            commands = create_goose_commands()
            
            # 步骤5: 测试HTTP接口
            if not test_http_interface():
                return 1
            
            # 步骤6: 创建集成指南
            guide = create_integration_guide()
            
            print_header("测试完成!")
            print("✅ 所有测试通过!")
            print("\n下一步:")
            print("1. 将MCP服务器配置到Goose中")
            print("2. 启动Goose: goose")
            print("3. 尝试说: \"执行pytest测试\"")
            print(f"\n配置文件: {config_file}")
            print("服务器运行在: http://localhost:8000")
            
            return 0
            
        finally:
            # 停止服务器
            print("\n停止MCP服务器...")
            server_process.terminate()
            server_process.wait()
            print("✓ 服务器已停止")
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # 确保在项目目录中
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 检查依赖
    try:
        import requests
    except ImportError:
        print("安装requests库: pip install requests")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    
    exit_code = main()
    sys.exit(exit_code)