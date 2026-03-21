"""
pytest运行器
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .models import (
    TestResult,
    TestCaseResult,
    TestStatus,
    PytestConfig,
    ExecutionContext,
)


async def run_pytest_tests(
    context: ExecutionContext,
    capture_output: bool = True,
) -> TestResult:
    """
    运行pytest测试
    
    Args:
        context: 执行上下文
        capture_output: 是否捕获输出
    
    Returns:
        TestResult: 测试结果
    """
    config = context.config
    result = TestResult(
        project_name=context.project_name,
        test_path=config.test_path,
        pytest_options=config.options,
        environment=config.environment,
        metadata=context.metadata,
        status="running",
    )
    
    try:
        # 构建pytest命令
        cmd = config.get_command()
        
        # 添加JSON报告选项
        if "--json-report" not in cmd and "-v" not in cmd:
            cmd.append("-v")
        
        # 设置环境变量
        env = {**config.environment, **dict(os.environ)}
        
        # 运行pytest
        start_time = datetime.now()
        
        if capture_output:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=Path.cwd(),
            )
            
            stdout, stderr = await process.communicate()
            return_code = process.returncode
        else:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                cwd=Path.cwd(),
            )
            
            await process.wait()
            return_code = process.returncode
            stdout = b""
            stderr = b""
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 解析结果
        result = parse_test_results(
            result,
            stdout.decode("utf-8") if capture_output else "",
            stderr.decode("utf-8") if capture_output else "",
            return_code,
            duration,
        )
        
        result.status = "completed" if return_code == 0 else "failed"
        result.completed_at = datetime.utcnow()
        
    except Exception as e:
        # 处理执行异常
        result.status = "failed"
        result.completed_at = datetime.utcnow()
        
        # 添加错误测试用例
        error_case = TestCaseResult(
            test_name="test_execution_error",
            node_id="",
            status=TestStatus.ERROR,
            error_message=str(e),
            stack_trace=traceback.format_exc(),
        )
        result.test_cases.append(error_case)
        result.errors += 1
        result.total_tests += 1
    
    return result


def parse_test_results(
    result: TestResult,
    stdout: str,
    stderr: str,
    return_code: int,
    duration: float,
) -> TestResult:
    """
    解析pytest输出结果
    
    Args:
        result: 测试结果对象
        stdout: 标准输出
        stderr: 标准错误
        return_code: 返回码
        duration: 执行时长
    
    Returns:
        TestResult: 更新后的测试结果
    """
    result.duration = duration
    
    # 简单的解析逻辑（实际项目中可以使用pytest的JSON报告）
    lines = stdout.split("\n")
    
    for line in lines:
        line = line.strip()
        
        # 解析测试结果行
        if line.startswith("test_"):
            # 简单解析测试结果
            # 实际项目中应该使用更复杂的解析逻辑或pytest的JSON报告
            if "PASSED" in line or "passed" in line:
                test_name = extract_test_name(line)
                if test_name:
                    case = TestCaseResult(
                        test_name=test_name,
                        node_id=test_name,
                        status=TestStatus.PASSED,
                    )
                    result.test_cases.append(case)
                    result.passed += 1
                    result.total_tests += 1
                    
            elif "FAILED" in line or "failed" in line:
                test_name = extract_test_name(line)
                if test_name:
                    case = TestCaseResult(
                        test_name=test_name,
                        node_id=test_name,
                        status=TestStatus.FAILED,
                        error_message="Test failed",
                    )
                    result.test_cases.append(case)
                    result.failed += 1
                    result.total_tests += 1
                    
            elif "SKIPPED" in line or "skipped" in line:
                test_name = extract_test_name(line)
                if test_name:
                    case = TestCaseResult(
                        test_name=test_name,
                        node_id=test_name,
                        status=TestStatus.SKIPPED,
                    )
                    result.test_cases.append(case)
                    result.skipped += 1
                    result.total_tests += 1
        
        # 解析统计信息
        elif "passed" in line and "failed" in line and "skipped" in line:
            # 解析类似 "3 passed, 1 failed, 2 skipped in 0.12s" 的行
            try:
                parts = line.split()
                for part in parts:
                    if part.endswith("passed"):
                        result.passed = int(part.split()[0])
                    elif part.endswith("failed"):
                        result.failed = int(part.split()[0])
                    elif part.endswith("skipped"):
                        result.skipped = int(part.split()[0])
                    elif part.endswith("error"):
                        result.errors = int(part.split()[0])
            except (ValueError, IndexError):
                pass
    
    # 如果没有解析到测试用例，尝试从stderr中获取错误信息
    if not result.test_cases and stderr:
        error_case = TestCaseResult(
            test_name="execution_error",
            node_id="",
            status=TestStatus.ERROR,
            error_message=stderr[:500],  # 限制长度
        )
        result.test_cases.append(error_case)
        result.errors += 1
        result.total_tests += 1
    
    return result


def extract_test_name(line: str) -> Optional[str]:
    """从输出行中提取测试名称"""
    # 简单的提取逻辑
    parts = line.split()
    for part in parts:
        if part.startswith("test_") and "[" not in part:
            return part
    return None


# 导入必要的模块
import os
import traceback