"""
pytest执行器数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class TestStatus(str, Enum):
    """测试状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    XFAIL = "xfail"
    XPASS = "xpass"


@dataclass
class TestCaseResult:
    """测试用例结果"""
    test_name: str
    node_id: str
    status: TestStatus
    duration: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_name": self.test_name,
            "node_id": self.node_id,
            "status": self.status.value,
            "duration": self.duration,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "metadata": self.metadata,
        }


@dataclass
class TestResult:
    """测试结果"""
    project_name: str
    test_path: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    status: str = "pending"
    pytest_options: List[str] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    test_cases: List[TestCaseResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_name": self.project_name,
            "test_path": self.test_path,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "duration": self.duration,
            "status": self.status,
            "success_rate": self.success_rate,
            "pytest_options": self.pytest_options,
            "environment": self.environment,
            "metadata": self.metadata,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class PytestConfig:
    """pytest配置"""
    test_path: str
    options: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[int] = None  # 超时时间（秒）
    max_workers: int = 1  # 最大工作进程数
    
    def get_command(self) -> List[str]:
        """获取pytest命令"""
        cmd = ["pytest", self.test_path]
        cmd.extend(self.options)
        return cmd


@dataclass
class ExecutionContext:
    """执行上下文"""
    config: PytestConfig
    project_name: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    callback_url: Optional[str] = None  # 进度回调URL