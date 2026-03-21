"""
MCP服务器
"""
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .handler import MCPHandler
from .models import MCPResponse
from ..config import settings
from ..database import Database, init_database, close_database


class MCPServer:
    """MCP服务器"""
    
    def __init__(self, database: Optional[Database] = None):
        self.app = FastAPI(
            title=settings.mcp_server_name,
            version=settings.mcp_server_version,
            description="MCP Pytest测试服务器",
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 初始化数据库
        self.database = database
        
        # 初始化MCP处理器
        self.handler = MCPHandler(database)
        
        # 注册路由
        self._setup_routes()
        
        # 注册生命周期事件
        self._setup_lifespan()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/")
        async def root():
            """根路径"""
            return {
                "name": settings.mcp_server_name,
                "version": settings.mcp_server_version,
                "description": "MCP Pytest测试服务器",
                "endpoints": {
                    "mcp": "/mcp",
                    "health": "/health",
                    "tools": "/tools",
                    "resources": "/resources",
                }
            }
        
        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: Request):
            """处理MCP请求"""
            try:
                # 解析请求体
                body = await request.body()
                request_data = json.loads(body)
                
                # 处理请求
                response = await self.handler.handle_request(request_data)
                
                # 返回响应
                return JSONResponse(
                    content=response.dict(exclude_none=True),
                    status_code=200,
                )
                
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
            except Exception as e:
                logging.error(f"MCP请求处理错误: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/tools")
        async def list_tools():
            """列出所有工具"""
            try:
                # 模拟MCP请求
                request_data = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                }
                
                response = await self.handler.handle_request(request_data)
                return JSONResponse(content=response.dict(exclude_none=True))
                
            except Exception as e:
                logging.error(f"获取工具列表错误: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/resources")
        async def list_resources():
            """列出所有资源"""
            try:
                # 模拟MCP请求
                request_data = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "resources/list",
                }
                
                response = await self.handler.handle_request(request_data)
                return JSONResponse(content=response.dict(exclude_none=True))
                
            except Exception as e:
                logging.error(f"获取资源列表错误: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/execute")
        async def execute_tests(request: Request):
            """执行测试（简化接口）"""
            try:
                body = await request.json()
                
                # 提取参数
                test_path = body.get("test_path")
                project_name = body.get("project_name", "default")
                pytest_options = body.get("pytest_options", ["-v", "--tb=short"])
                
                if not test_path:
                    raise HTTPException(status_code=400, detail="test_path is required")
                
                # 调用工具
                request_data = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "run_pytest_tests",
                        "arguments": {
                            "test_path": test_path,
                            "project_name": project_name,
                            "pytest_options": pytest_options,
                        }
                    }
                }
                
                response = await self.handler.handle_request(request_data)
                return JSONResponse(content=response.dict(exclude_none=True))
                
            except Exception as e:
                logging.error(f"执行测试错误: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
    
    def _setup_lifespan(self):
        """设置生命周期"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """启动事件"""
            logging.info(f"Starting {settings.mcp_server_name} v{settings.mcp_server_version}")
            
            # 初始化数据库
            if self.database:
                await init_database()
                logging.info("Database initialized")
            
            logging.info(f"Server listening on {settings.host}:{settings.port}")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """关闭事件"""
            logging.info("Shutting down server...")
            
            # 关闭数据库
            if self.database:
                await close_database()
                logging.info("Database closed")
            
            logging.info("Server shutdown complete")
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """运行服务器"""
        import uvicorn
        
        uvicorn.run(
            self.app,
            host=host or settings.host,
            port=port or settings.port,
            log_level=settings.log_level.lower(),
            reload=settings.debug,
        )


# 导入必要的模块
import datetime
import logging

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)