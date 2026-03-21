"""
MCP协议数据模型
"""
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class MCPMessageType(str, Enum):
    """MCP消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class MCPErrorCode(str, Enum):
    """MCP错误码"""
    INVALID_REQUEST = "invalid_request"
    METHOD_NOT_FOUND = "method_not_found"
    INVALID_PARAMS = "invalid_params"
    INTERNAL_ERROR = "internal_error"
    SERVER_ERROR = "server_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    TOOL_NOT_FOUND = "tool_not_found"
    TOOL_EXECUTION_ERROR = "tool_execution_error"


class MCPServerInfo(BaseModel):
    """MCP服务器信息"""
    name: str = Field(..., description="服务器名称")
    version: str = Field(..., description="服务器版本")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="服务器能力")


class MCPTool(BaseModel):
    """MCP工具定义"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    inputSchema: Dict[str, Any] = Field(..., description="输入模式")
    outputSchema: Optional[Dict[str, Any]] = Field(None, description="输出模式")


class MCPResource(BaseModel):
    """MCP资源定义"""
    uri: str = Field(..., description="资源URI")
    name: str = Field(..., description="资源名称")
    description: Optional[str] = Field(None, description="资源描述")
    mimeType: str = Field("text/plain", description="MIME类型")


class MCPRequest(BaseModel):
    """MCP请求"""
    jsonrpc: str = Field("2.0", description="JSON-RPC版本")
    id: Optional[Union[str, int]] = Field(None, description="请求ID")
    method: str = Field(..., description="方法名")
    params: Optional[Dict[str, Any]] = Field(None, description="参数")


class MCPResponse(BaseModel):
    """MCP响应"""
    jsonrpc: str = Field("2.0", description="JSON-RPC版本")
    id: Optional[Union[str, int]] = Field(None, description="请求ID")
    result: Optional[Any] = Field(None, description="结果")
    error: Optional[Dict[str, Any]] = Field(None, description="错误信息")


class MCPError(BaseModel):
    """MCP错误"""
    code: MCPErrorCode = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    data: Optional[Dict[str, Any]] = Field(None, description="错误数据")


# 初始化相关模型
class MCPInitializeRequest(BaseModel):
    """初始化请求"""
    protocolVersion: str = Field(..., description="协议版本")
    clientInfo: Optional[Dict[str, Any]] = Field(None, description="客户端信息")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="客户端能力")


class MCPInitializeResult(BaseModel):
    """初始化结果"""
    protocolVersion: str = Field(..., description="协议版本")
    serverInfo: MCPServerInfo = Field(..., description="服务器信息")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="服务器能力")


# 工具相关模型
class MCPToolsListRequest(BaseModel):
    """工具列表请求"""
    pass


class MCPToolsListResult(BaseModel):
    """工具列表结果"""
    tools: List[MCPTool] = Field(..., description="工具列表")


class MCPToolsCallRequest(BaseModel):
    """工具调用请求"""
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(..., description="参数")


class MCPToolsCallResult(BaseModel):
    """工具调用结果"""
    content: List[Dict[str, Any]] = Field(..., description="内容")
    isError: bool = Field(False, description="是否为错误")


# 资源相关模型
class MCPResourcesListRequest(BaseModel):
    """资源列表请求"""
    pass


class MCPResourcesListResult(BaseModel):
    """资源列表结果"""
    resources: List[MCPResource] = Field(..., description="资源列表")


class MCPResourcesReadRequest(BaseModel):
    """资源读取请求"""
    uri: str = Field(..., description="资源URI")


class MCPResourcesReadResult(BaseModel):
    """资源读取结果"""
    contents: List[Dict[str, Any]] = Field(..., description="内容列表")
    mimeType: str = Field("text/plain", description="MIME类型")


# 通知相关模型
class MCPNotification(BaseModel):
    """MCP通知"""
    jsonrpc: str = Field("2.0", description="JSON-RPC版本")
    method: str = Field(..., description="方法名")
    params: Optional[Dict[str, Any]] = Field(None, description="参数")


class MCPProgressNotification(BaseModel):
    """进度通知"""
    progressToken: str = Field(..., description="进度令牌")
    progress: float = Field(..., description="进度(0-1)")
    message: Optional[str] = Field(None, description="进度消息")