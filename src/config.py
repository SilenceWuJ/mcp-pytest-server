"""
配置管理模块
"""
import os
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8000, description="服务器监听端口")
    debug: bool = Field(default=False, description="调试模式")
    
    # # 数据库配置
    # database_url: str = Field(
    #     default="sqlite:///./test_results.db",
    #     description="数据库连接URL"
    # )
    database_url: str = Field(
        default="mysql+pymysql://qa_user:123456@localhost:3306/qa_platform",
        description="数据库连接URL"
    )
    
    # MCP配置
    mcp_server_name: str = Field(
        default="pytest-test-server",
        description="MCP服务器名称"
    )
    mcp_server_version: str = Field(
        default="0.1.0",
        description="MCP服务器版本"
    )
    
    # pytest配置
    pytest_default_options: List[str] = Field(
        default=["-v", "--tb=short"],
        description="pytest默认选项"
    )
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    
    class Config:
        env_file = ".env"
        env_prefix = "MCP_PYTEST_"
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """验证数据库URL"""
        if not v:
            raise ValueError("数据库URL不能为空")
        return v
    
    @validator("pytest_default_options")
    def validate_pytest_options(cls, v):
        """验证pytest选项"""
        if not isinstance(v, list):
            raise ValueError("pytest选项必须是列表")
        return v


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings