#!/usr/bin/env python3
"""
简化版MCP服务器 - 用于快速测试
"""
import json
import asyncio
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import subprocess
import sys
import os

app = FastAPI(title="MCP Pytest Test Server", version="0.1.0")

# 内存存储（简化版，不使用数据库）
test_history = []

class TestResult:
    """测试结果"""
    def __init__(self, project_name: str, test_path: str):
        self.project_name = project_name
        self.test_path = test_path
        self.total_tests = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.duration = 0.0
        self.status = "pending"
        self.test_cases = []
    
    def to_dict(self):
        return {
            "project_name": self.project_name,
            "test_path": self.test_path,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration": self.duration,
            "status": self.status,
            "success_rate": (self.passed / self.total_tests * 100) if self.total_tests > 0 else 0,
            "test_cases": self.test_cases
        }

async def run_pytest_simple(test_path: str, options: List[str] = None) -> TestResult:
    """运行pytest测试（简化版）"""
    if options is None:
        options = ["-v", "--tb=short"]
    
    result = TestResult("default", test_path)
    
    try:
        # 构建命令
        cmd = ["pytest", test_path] + options
        
        # 运行测试
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        stdout, stderr = await process.communicate()
        return_code = process.returncode
        
        # 解析结果（简化版）
        output = stdout.decode('utf-8')
        
        # 简单解析
        lines = output.split('\n')
        for line in lines:
            if "passed" in line and "failed" in line and "skipped" in line:
                # 解析统计行，如: "3 passed, 1 failed, 2 skipped in 0.12s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.endswith("passed"):
                        result.passed = int(parts[i-1])
                    elif part.endswith("failed"):
                        result.failed = int(parts[i-1])
                    elif part.endswith("skipped"):
                        result.skipped = int(parts[i-1])
        
        result.total_tests = result.passed + result.failed + result.skipped
        result.status = "completed" if return_code == 0 else "failed"
        
        # 添加到历史
        test_history.append(result.to_dict())
        
    except Exception as e:
        result.status = "failed"
        result.test_cases.append({
            "name": "execution_error",
            "status": "error",
            "error": str(e)
        })
    
    return result

# MCP协议端点
@app.post("/mcp")
async def handle_mcp(request: Request):
    """处理MCP请求"""
    try:
        data = await request.json()
        
        method = data.get("method")
        params = data.get("params", {})
        
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "pytest-test-server",
                        "version": "0.1.0"
                    },
                    "capabilities": {}
                }
            }
        
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "run_pytest_tests",
                            "description": "执行pytest测试",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "test_path": {"type": "string"},
                                    "project_name": {"type": "string", "default": "default"},
                                    "pytest_options": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "default": ["-v", "--tb=short"]
                                    }
                                },
                                "required": ["test_path"]
                            }
                        },
                        {
                            "name": "get_test_history",
                            "description": "获取测试历史",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "default": 10}
                                }
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "run_pytest_tests":
                test_path = arguments.get("test_path")
                if not test_path:
                    raise HTTPException(status_code=400, detail="test_path is required")
                
                result = await run_pytest_simple(
                    test_path,
                    arguments.get("pytest_options", ["-v", "--tb=short"])
                )
                
                response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"测试执行完成！\n\n"
                                       f"项目: {result.project_name}\n"
                                       f"测试路径: {test_path}\n"
                                       f"状态: {result.status}\n"
                                       f"总测试数: {result.total_tests}\n"
                                       f"通过: {result.passed}\n"
                                       f"失败: {result.failed}\n"
                                       f"跳过: {result.skipped}\n"
                                       f"成功率: {result.to_dict()['success_rate']:.1f}%\n"
                            }
                        ],
                        "isError": result.status == "failed"
                    }
                }
            
            elif tool_name == "get_test_history":
                limit = arguments.get("limit", 10)
                history = test_history[-limit:] if test_history else []
                
                response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"测试历史记录 ({len(history)}条):\n\n" + 
                                       "\n".join([
                                           f"{i+1}. {item['project_name']} - {item['test_path']} - "
                                           f"{item['passed']}/{item['total_tests']} 通过 ({item['success_rate']:.1f}%)"
                                           for i, item in enumerate(history)
                                       ])
                            }
                        ],
                        "isError": False
                    }
                }
            
            else:
                raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
        
        else:
            raise HTTPException(status_code=404, detail=f"Method not found: {method}")
        
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 简化HTTP接口
@app.get("/")
async def root():
    return {
        "name": "MCP Pytest Test Server",
        "version": "0.1.0",
        "description": "简化版MCP服务器，用于快速测试",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health",
            "execute": "/execute (POST)"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/execute")
async def execute_tests(request: Request):
    """执行测试（简化接口）"""
    try:
        data = await request.json()
        test_path = data.get("test_path")
        
        if not test_path:
            raise HTTPException(status_code=400, detail="test_path is required")
        
        result = await run_pytest_simple(test_path)
        
        return {
            "success": result.status == "completed",
            "result": result.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("简化版MCP Pytest测试服务器")
    print("版本: 0.1.0")
    print("=" * 60)
    print("\n端点:")
    print("  • MCP接口: http://localhost:8000/mcp")
    print("  • 健康检查: http://localhost:8000/health")
    print("  • 执行测试: http://localhost:8000/execute (POST)")
    print("\n可用工具:")
    print("  • run_pytest_tests - 执行pytest测试")
    print("  • get_test_history - 获取测试历史")
    print("\n" + "=" * 60)
    print("服务器正在启动... (按 Ctrl+C 停止)")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")