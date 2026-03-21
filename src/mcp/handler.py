"""
MCP请求处理器
"""
import json
from typing import Dict, Any, Optional, Callable, List
from functools import wraps

from .models import (
    MCPRequest,
    MCPResponse,
    MCPError,
    MCPErrorCode,
    MCPInitializeRequest,
    MCPInitializeResult,
    MCPToolsListRequest,
    MCPToolsListResult,
    MCPToolsCallRequest,
    MCPToolsCallResult,
    MCPResourcesListRequest,
    MCPResourcesListResult,
    MCPResourcesReadRequest,
    MCPResourcesReadResult,
    MCPServerInfo,
    MCPTool,
    MCPResource,
)
from ..config import settings
from ..pytest_executor import PytestExecutor, ExecutionContext, PytestConfig
from ..database import Database


class MCPHandler:
    """MCP请求处理器"""
    
    def __init__(self, database: Optional[Database] = None):
        self.database = database
        self.pytest_executor = PytestExecutor(database)
        self.tools: Dict[str, Callable] = {}
        self.resources: Dict[str, MCPResource] = {}
        
        # 注册默认工具
        self._register_default_tools()
        self._register_default_resources()
    
    def _register_default_tools(self):
        """注册默认工具"""
        self.register_tool(
            name="run_pytest_tests",
            description="执行pytest测试",
            input_schema={
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "测试路径或文件"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "项目名称",
                        "default": "default"
                    },
                    "pytest_options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "pytest选项",
                        "default": ["-v", "--tb=short"]
                    },
                    "environment": {
                        "type": "object",
                        "description": "环境变量",
                        "default": {}
                    },
                    "store_to_db": {
                        "type": "boolean",
                        "description": "是否存储到数据库",
                        "default": True
                    }
                },
                "required": ["test_path"]
            },
            handler=self._handle_run_pytest_tests
        )
        
        self.register_tool(
            name="get_test_history",
            description="获取测试历史记录",
            input_schema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "项目名称"
                    },
                    "days": {
                        "type": "integer",
                        "description": "查询天数",
                        "default": 7
                    },
                    "limit": {
                        "type": "integer",
                        "description": "限制数量",
                        "default": 50
                    }
                }
            },
            handler=self._handle_get_test_history
        )
        
        self.register_tool(
            name="get_project_stats",
            description="获取项目统计信息",
            input_schema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "项目名称",
                        "required": True
                    },
                    "days": {
                        "type": "integer",
                        "description": "统计天数",
                        "default": 30
                    }
                }
            },
            handler=self._handle_get_project_stats
        )
        
        self.register_tool(
            name="get_test_run_details",
            description="获取测试运行详情",
            input_schema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "integer",
                        "description": "测试运行ID",
                        "required": True
                    }
                }
            },
            handler=self._handle_get_test_run_details
        )
    
    def _register_default_resources(self):
        """注册默认资源"""
        self.register_resource(
            uri="server://info",
            name="服务器信息",
            description="MCP服务器信息",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="server://tools",
            name="工具列表",
            description="可用工具列表",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="server://resources",
            name="资源列表",
            description="可用资源列表",
            mime_type="application/json"
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
        output_schema: Optional[Dict[str, Any]] = None,
    ):
        """注册工具"""
        self.tools[name] = {
            "handler": handler,
            "tool": MCPTool(
                name=name,
                description=description,
                inputSchema=input_schema,
                outputSchema=output_schema,
            )
        }
    
    def register_resource(
        self,
        uri: str,
        name: str,
        description: Optional[str] = None,
        mime_type: str = "text/plain",
    ):
        """注册资源"""
        self.resources[uri] = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mimeType=mime_type,
        )
    
    async def handle_request(self, request_data: Dict[str, Any]) -> MCPResponse:
        """处理MCP请求"""
        try:
            request = MCPRequest(**request_data)
            
            # 根据方法名路由请求
            if request.method == "initialize":
                result = await self._handle_initialize(request.params)
            elif request.method == "tools/list":
                result = await self._handle_tools_list(request.params)
            elif request.method == "tools/call":
                result = await self._handle_tools_call(request.params)
            elif request.method == "resources/list":
                result = await self._handle_resources_list(request.params)
            elif request.method == "resources/read":
                result = await self._handle_resources_read(request.params)
            else:
                raise MCPError(
                    code=MCPErrorCode.METHOD_NOT_FOUND,
                    message=f"Method not found: {request.method}"
                )
            
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                result=result.dict() if hasattr(result, "dict") else result,
            )
            
        except MCPError as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request_data.get("id"),
                error={
                    "code": e.code.value,
                    "message": e.message,
                    "data": e.data,
                },
            )
        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request_data.get("id"),
                error={
                    "code": MCPErrorCode.INTERNAL_ERROR.value,
                    "message": f"Internal error: {str(e)}",
                },
            )
    
    async def _handle_initialize(self, params: Optional[Dict[str, Any]]) -> MCPInitializeResult:
        """处理初始化请求"""
        if params:
            request = MCPInitializeRequest(**params)
        else:
            request = MCPInitializeRequest(
                protocolVersion="2024-11-05",
                clientInfo={},
                capabilities={},
            )
        
        server_info = MCPServerInfo(
            name=settings.mcp_server_name,
            version=settings.mcp_server_version,
            capabilities={
                "tools": {},
                "resources": {},
            }
        )
        
        return MCPInitializeResult(
            protocolVersion=request.protocolVersion,
            serverInfo=server_info,
            capabilities={
                "tools": {},
                "resources": {},
            }
        )
    
    async def _handle_tools_list(self, params: Optional[Dict[str, Any]]) -> MCPToolsListResult:
        """处理工具列表请求"""
        if params:
            request = MCPToolsListRequest(**params)
        else:
            request = MCPToolsListRequest()
        
        tools = [tool_info["tool"] for tool_info in self.tools.values()]
        return MCPToolsListResult(tools=tools)
    
    async def _handle_tools_call(self, params: Optional[Dict[str, Any]]) -> MCPToolsCallResult:
        """处理工具调用请求"""
        if not params:
            raise MCPError(
                code=MCPErrorCode.INVALID_PARAMS,
                message="Missing parameters for tools/call"
            )
        
        request = MCPToolsCallRequest(**params)
        
        if request.name not in self.tools:
            raise MCPError(
                code=MCPErrorCode.TOOL_NOT_FOUND,
                message=f"Tool not found: {request.name}"
            )
        
        tool_info = self.tools[request.name]
        handler = tool_info["handler"]
        
        try:
            result = await handler(request.arguments)
            
            if isinstance(result, dict) and "content" in result:
                # 已经是MCPToolsCallResult格式
                content = result["content"]
                is_error = result.get("isError", False)
            else:
                # 包装结果
                content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                is_error = False
            
            return MCPToolsCallResult(
                content=content,
                isError=is_error,
            )
            
        except Exception as e:
            raise MCPError(
                code=MCPErrorCode.TOOL_EXECUTION_ERROR,
                message=f"Tool execution error: {str(e)}",
                data={"tool": request.name}
            )
    
    async def _handle_resources_list(self, params: Optional[Dict[str, Any]]) -> MCPResourcesListResult:
        """处理资源列表请求"""
        if params:
            request = MCPResourcesListRequest(**params)
        else:
            request = MCPResourcesListRequest()
        
        resources = list(self.resources.values())
        return MCPResourcesListResult(resources=resources)
    
    async def _handle_resources_read(self, params: Optional[Dict[str, Any]]) -> MCPResourcesReadResult:
        """处理资源读取请求"""
        if not params:
            raise MCPError(
                code=MCPErrorCode.INVALID_PARAMS,
                message="Missing parameters for resources/read"
            )
        
        request = MCPResourcesReadRequest(**params)
        
        if request.uri not in self.resources:
            raise MCPError(
                code=MCPErrorCode.RESOURCE_NOT_FOUND,
                message=f"Resource not found: {request.uri}"
            )
        
        resource = self.resources[request.uri]
        
        # 根据URI返回不同的内容
        if request.uri == "server://info":
            content = {
                "name": settings.mcp_server_name,
                "version": settings.mcp_server_version,
                "description": "MCP Pytest测试服务器",
                "capabilities": ["tools", "resources"],
            }
        elif request.uri == "server://tools":
            tools = [tool_info["tool"].dict() for tool_info in self.tools.values()]
            content = {"tools": tools}
        elif request.uri == "server://resources":
            resources = [resource.dict() for resource in self.resources.values()]
            content = {"resources": resources}
        else:
            content = {"message": f"Resource: {request.uri}"}
        
        return MCPResourcesReadResult(
            contents=[{"uri": request.uri, "text": json.dumps(content, ensure_ascii=False, indent=2)}],
            mimeType=resource.mimeType,
        )
    
    # 工具处理函数
    async def _handle_run_pytest_tests(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理运行pytest测试工具"""
        test_path = arguments["test_path"]
        project_name = arguments.get("project_name", "default")
        pytest_options = arguments.get("pytest_options", ["-v", "--tb=short"])
        environment = arguments.get("environment", {})
        store_to_db = arguments.get("store_to_db", True)
        
        # 创建执行上下文
        config = PytestConfig(
            test_path=test_path,
            options=pytest_options,
            environment=environment,
        )
        
        context = ExecutionContext(
            config=config,
            project_name=project_name,
            metadata={
                "source": "mcp_tool",
                "arguments": arguments,
            }
        )
        
        # 执行测试
        test_result = await self.pytest_executor.execute_tests(
            context=context,
            store_to_db=store_to_db,
        )
        
        # 格式化结果
        result_dict = test_result.to_dict()
        
        # 创建MCP格式的响应
        content = [
            {
                "type": "text",
                "text": f"测试执行完成！\n\n"
                       f"项目: {project_name}\n"
                       f"测试路径: {test_path}\n"
                       f"状态: {test_result.status}\n"
                       f"总测试数: {test_result.total_tests}\n"
                       f"通过: {test_result.passed}\n"
                       f"失败: {test_result.failed}\n"
                       f"跳过: {test_result.skipped}\n"
                       f"错误: {test_result.errors}\n"
                       f"成功率: {test_result.success_rate:.1f}%\n"
                       f"耗时: {test_result.duration:.2f}秒\n"
            }
        ]
        
        if test_result.failed > 0 or test_result.errors > 0:
            # 添加失败详情
            failed_cases = [
                tc for tc in test_result.test_cases 
                if tc.status in ["failed", "error"]
            ]
            
            if failed_cases:
                content.append({
                    "type": "text",
                    "text": f"\n失败的测试用例 ({len(failed_cases)}个):\n" + 
                           "\n".join([f"- {tc.test_name}: {tc.error_message or 'No error message'}" 
                                     for tc in failed_cases[:10]])  # 限制显示数量
                })
        
        return {
            "content": content,
            "isError": test_result.status == "failed",
            "raw_result": result_dict,
        }
    
    async def _handle_get_test_history(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取测试历史工具"""
        if not self.database:
            return {
                "content": [{"type": "text", "text": "数据库未连接"}],
                "isError": True,
            }
        
        project_name = arguments.get("project_name")
        days = arguments.get("days", 7)
        limit = arguments.get("limit", 50)
        
        async with self.database.get_session() as session:
            from ..database import get_test_history
            history = await get_test_history(
                session=session,
                project_name=project_name,
                days=days,
                limit=limit,
            )
        
        if not history:
            return {
                "content": [{"type": "text", "text": "没有找到测试历史记录"}],
                "isError": False,
            }
        
        # 格式化历史记录
        text = f"测试历史记录 ({len(history)}条):\n\n"
        for run in history:
            text += f"ID: {run['id']}\n"
            text += f"项目: {run['project_name']}\n"
            text += f"路径: {run['test_path']}\n"
            text += f"状态: {run['status']}\n"
            text += f"结果: {run['passed']}/{run['total_tests']} 通过 ({run['success_rate']:.1f}%)\n"
            text += f"时间: {run['created_at']}\n"
            text += "-" * 50 + "\n"
        
        return {
            "content": [{"type": "text", "text": text}],
            "isError": False,
            "raw_result": history,
        }
    
    async def _handle_get_project_stats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取项目统计工具"""
        if not self.database:
            return {
                "content": [{"type": "text", "text": "数据库未连接"}],
                "isError": True,
            }
        
        project_name = arguments["project_name"]
        days = arguments.get("days", 30)
        
        async with self.database.get_session() as session:
            from ..database import get_project_stats
            stats = await get_project_stats(
                session=session,
                project_name=project_name,
                days=days,
            )
        
        # 格式化统计信息
        text = f"项目统计: {project_name}\n"
        text += f"统计周期: 最近{days}天\n\n"
        text += f"总运行次数: {stats['total_runs']}\n"
        text += f"总测试用例数: {stats['total_tests']}\n"
        text += f"通过: {stats['total_passed']}\n"
        text += f"失败: {stats['total_failed']}\n"
        text += f"跳过: {stats['total_skipped']}\n"
        text += f"平均成功率: {stats['avg_success_rate']:.1f}%\n"
        text += f"最近成功率: {stats['recent_success_rate']:.1f}%\n"
        text += f"平均执行时间: {stats['avg_duration']:.2f}秒\n"
        text += f"最后更新: {stats['last_updated']}\n"
        
        return {
            "content": [{"type": "text", "text": text}],
            "isError": False,
            "raw_result": stats,
        }
    
    async def _handle_get_test_run_details(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取测试运行详情工具"""
        if not self.database:
            return {
                "content": [{"type": "text", "text": "数据库未连接"}],
                "isError": True,
            }
        
        run_id = arguments["run_id"]
        
        async with self.database.get_session() as session:
            from ..database import get_test_run, get_test_cases_by_run
            test_run = await get_test_run(session, run_id)
            
            if not test_run:
                return {
                    "content": [{"type": "text", "text": f"未找到测试运行记录: {run_id}"}],
                    "isError": True,
                }
            
            test_cases = await get_test_cases_by_run(session, run_id)
        
        # 格式化详情
        text = f"测试运行详情 ID: {run_id}\n\n"
        text += f"项目: {test_run.project_name}\n"
        text += f"测试路径: {test_run.test_path}\n"
        text += f"状态: {test_run.status}\n"
        text += f"总测试数: {test_run.total_tests}\n"
        text += f"通过: {test_run.passed}\n"
        text += f"失败: {test_run.failed}\n"
        text += f"跳过: {test_run.skipped}\n"
        text += f"错误: {test_run.errors}\n"
        text += f"成功率: {test_run.success_rate:.1f}%\n"
        text += f"耗时: {test_run.duration:.2f}秒\n"
        text += f"创建时间: {test_run.created_at}\n"
        text += f"完成时间: {test_run.completed_at}\n\n"
        
        if test_cases:
            text += f"测试用例详情 ({len(test_cases)}个):\n\n"
            for i, test_case in enumerate(test_cases, 1):
                text += f"{i}. {test_case.test_name}\n"
                text += f"   状态: {test_case.status}\n"
                text += f"   耗时: {test_case.duration:.2f}秒\n"
                if test_case.error_message:
                    text += f"   错误: {test_case.error_message[:100]}...\n"
                text += "\n"
        
        return {
            "content": [{"type": "text", "text": text}],
            "isError": False,
            "raw_result": {
                "test_run": test_run.to_dict(),
                "test_cases": [tc.to_dict() for tc in test_cases],
            },
        }