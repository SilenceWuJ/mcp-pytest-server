"""
数据库模型定义
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr

Base = declarative_base()


class TestRun(Base):
    """测试运行记录"""
    __tablename__ = "test_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255), nullable=False, index=True)
    test_path = Column(String(500), nullable=False)
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    duration = Column(Float, default=0.0)  # 单位：秒
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    test_cases = relationship("TestCase", back_populates="test_run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TestRun(id={self.id}, project={self.project_name}, status={self.status})>"
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100
    
    @property
    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.status in ["completed", "failed"]
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "project_name": self.project_name,
            "test_path": self.test_path,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration": self.duration,
            "status": self.status,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TestCase(Base):
    """测试用例记录"""
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    test_name = Column(String(500), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # passed, failed, skipped, error
    duration = Column(Float, default=0.0)  # 单位：秒
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    test_run = relationship("TestRun", back_populates="test_cases")
    
    def __repr__(self):
        return f"<TestCase(id={self.id}, name={self.test_name}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "test_name": self.test_name,
            "status": self.status,
            "duration": self.duration,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Project(Base):
    """项目配置"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    default_test_path = Column(String(500), nullable=True)
    default_pytest_options = Column(JSON, default=list)
    environment_vars = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "default_test_path": self.default_test_path,
            "default_pytest_options": self.default_pytest_options,
            "environment_vars": self.environment_vars,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }