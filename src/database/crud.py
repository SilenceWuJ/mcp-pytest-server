"""
数据库CRUD操作
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import TestRun, TestCase, Project
from .connection import db


async def create_test_run(
    session: AsyncSession,
    project_name: str,
    test_path: str,
    total_tests: int = 0,
    passed: int = 0,
    failed: int = 0,
    skipped: int = 0,
    duration: float = 0.0,
    status: str = "pending",
) -> TestRun:
    """创建测试运行记录"""
    test_run = TestRun(
        project_name=project_name,
        test_path=test_path,
        total_tests=total_tests,
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration=duration,
        status=status,
        created_at=datetime.utcnow(),
    )
    
    session.add(test_run)
    await session.commit()
    await session.refresh(test_run)
    
    return test_run


async def get_test_run(session: AsyncSession, run_id: int) -> Optional[TestRun]:
    """获取测试运行记录"""
    stmt = select(TestRun).where(TestRun.id == run_id).options(selectinload(TestRun.test_cases))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_test_runs(
    session: AsyncSession,
    project_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[TestRun]:
    """获取测试运行记录列表"""
    stmt = select(TestRun).options(selectinload(TestRun.test_cases))
    
    # 添加过滤条件
    filters = []
    if project_name:
        filters.append(TestRun.project_name == project_name)
    if status:
        filters.append(TestRun.status == status)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    # 排序和分页
    stmt = stmt.order_by(TestRun.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_test_run(
    session: AsyncSession,
    run_id: int,
    **kwargs,
) -> Optional[TestRun]:
    """更新测试运行记录"""
    # 构建更新数据
    update_data = {}
    for key, value in kwargs.items():
        if hasattr(TestRun, key) and value is not None:
            update_data[key] = value
    
    if not update_data:
        return None
    
    # 如果是完成状态，设置完成时间
    if "status" in update_data and update_data["status"] in ["completed", "failed"]:
        update_data["completed_at"] = datetime.utcnow()
    
    stmt = (
        update(TestRun)
        .where(TestRun.id == run_id)
        .values(**update_data)
        .returning(TestRun)
    )
    
    result = await session.execute(stmt)
    await session.commit()
    
    return result.scalar_one_or_none()


async def delete_test_run(session: AsyncSession, run_id: int) -> bool:
    """删除测试运行记录"""
    stmt = delete(TestRun).where(TestRun.id == run_id)
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount > 0


async def create_test_case(
    session: AsyncSession,
    run_id: int,
    test_name: str,
    status: str,
    duration: float = 0.0,
    error_message: Optional[str] = None,
    stack_trace: Optional[str] = None,
) -> TestCase:
    """创建测试用例记录"""
    test_case = TestCase(
        run_id=run_id,
        test_name=test_name,
        status=status,
        duration=duration,
        error_message=error_message,
        stack_trace=stack_trace,
        created_at=datetime.utcnow(),
    )
    
    session.add(test_case)
    await session.commit()
    await session.refresh(test_case)
    
    return test_case


async def get_test_cases_by_run(
    session: AsyncSession,
    run_id: int,
    status: Optional[str] = None,
) -> List[TestCase]:
    """获取测试运行的所有测试用例"""
    stmt = select(TestCase).where(TestCase.run_id == run_id)
    
    if status:
        stmt = stmt.where(TestCase.status == status)
    
    stmt = stmt.order_by(TestCase.id)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_test_history(
    session: AsyncSession,
    project_name: Optional[str] = None,
    days: int = 7,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """获取测试历史记录"""
    # 计算时间范围
    start_date = datetime.utcnow() - timedelta(days=days)
    
    stmt = select(TestRun).where(TestRun.created_at >= start_date)
    
    if project_name:
        stmt = stmt.where(TestRun.project_name == project_name)
    
    stmt = stmt.order_by(TestRun.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    test_runs = list(result.scalars().all())
    
    # 转换为字典格式
    history = []
    for run in test_runs:
        history.append(run.to_dict())
    
    return history


async def get_project_stats(
    session: AsyncSession,
    project_name: str,
    days: int = 30,
) -> Dict[str, Any]:
    """获取项目统计信息"""
    # 计算时间范围
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 查询测试运行统计
    stmt = select(
        func.count(TestRun.id).label("total_runs"),
        func.sum(TestRun.total_tests).label("total_tests"),
        func.sum(TestRun.passed).label("total_passed"),
        func.sum(TestRun.failed).label("total_failed"),
        func.sum(TestRun.skipped).label("total_skipped"),
        func.avg(TestRun.duration).label("avg_duration"),
    ).where(
        and_(
            TestRun.project_name == project_name,
            TestRun.created_at >= start_date,
            TestRun.status == "completed",
        )
    )
    
    result = await session.execute(stmt)
    stats = result.first()
    
    # 查询最近的成功率
    recent_stmt = select(TestRun).where(
        and_(
            TestRun.project_name == project_name,
            TestRun.created_at >= start_date,
            TestRun.status == "completed",
        )
    ).order_by(TestRun.created_at.desc()).limit(10)
    
    recent_result = await session.execute(recent_stmt)
    recent_runs = list(recent_result.scalars().all())
    
    recent_success_rates = [run.success_rate for run in recent_runs if run.total_tests > 0]
    avg_recent_success_rate = sum(recent_success_rates) / len(recent_success_rates) if recent_success_rates else 0
    
    return {
        "project_name": project_name,
        "period_days": days,
        "total_runs": stats.total_runs or 0,
        "total_tests": stats.total_tests or 0,
        "total_passed": stats.total_passed or 0,
        "total_failed": stats.total_failed or 0,
        "total_skipped": stats.total_skipped or 0,
        "avg_duration": float(stats.avg_duration or 0),
        "avg_success_rate": (stats.total_passed / stats.total_tests * 100) if stats.total_tests and stats.total_tests > 0 else 0,
        "recent_success_rate": avg_recent_success_rate,
        "last_updated": datetime.utcnow().isoformat(),
    }


async def create_project(
    session: AsyncSession,
    name: str,
    description: Optional[str] = None,
    default_test_path: Optional[str] = None,
    default_pytest_options: Optional[List[str]] = None,
    environment_vars: Optional[Dict[str, str]] = None,
) -> Project:
    """创建项目配置"""
    project = Project(
        name=name,
        description=description,
        default_test_path=default_test_path,
        default_pytest_options=default_pytest_options or [],
        environment_vars=environment_vars or {},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    session.add(project)
    await session.commit()
    await session.refresh(project)
    
    return project


async def get_project(session: AsyncSession, name: str) -> Optional[Project]:
    """获取项目配置"""
    stmt = select(Project).where(Project.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()