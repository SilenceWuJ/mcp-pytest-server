"""
数据库CRUD操作 - 新版
支持测试用例、测试分析、HTML测试报告和项目详细信息
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union, BinaryIO
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import json
import base64

from .models import (
    Base, TestRun, TestCase, Project, HTMLReport, TestAnalysis, TestHistory,
    TestRunStatus, TestCaseStatus
)


# ==================== 项目相关操作 ====================

async def create_project(
    session: AsyncSession,
    name: str,
    description: Optional[str] = None,
    repository_url: Optional[str] = None,
    branch: str = "main",
    default_test_path: Optional[str] = None,
    default_pytest_options: Optional[List[str]] = None,
    environment_vars: Optional[Dict[str, str]] = None,
    notification_config: Optional[Dict[str, Any]] = None,
    is_active: bool = True,
) -> Project:
    """创建项目配置"""
    project = Project(
        name=name,
        description=description,
        repository_url=repository_url,
        branch=branch,
        default_test_path=default_test_path,
        default_pytest_options=default_pytest_options or [],
        environment_vars=environment_vars or {},
        notification_config=notification_config or {},
        is_active=is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    session.add(project)
    await session.commit()
    await session.refresh(project)
    
    return project


async def get_project(session: AsyncSession, project_id: int) -> Optional[Project]:
    """根据ID获取项目配置"""
    stmt = select(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_project_by_name(session: AsyncSession, name: str) -> Optional[Project]:
    """根据名称获取项目配置"""
    stmt = select(Project).where(Project.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_projects(
    session: AsyncSession,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Project]:
    """获取项目列表"""
    stmt = select(Project)
    
    if is_active is not None:
        stmt = stmt.where(Project.is_active == is_active)
    
    stmt = stmt.order_by(Project.created_at.desc()).limit(limit).offset(offset)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_project(
    session: AsyncSession,
    project_id: int,
    **kwargs,
) -> Optional[Project]:
    """更新项目配置"""
    update_data = {}
    for key, value in kwargs.items():
        if hasattr(Project, key) and value is not None:
            update_data[key] = value
    
    if not update_data:
        return None
    
    # 更新更新时间
    update_data["updated_at"] = datetime.utcnow()
    
    stmt = (
        update(Project)
        .where(Project.id == project_id)
        .values(**update_data)
        .returning(Project)
    )
    
    result = await session.execute(stmt)
    await session.commit()
    
    return result.scalar_one_or_none()


async def delete_project(session: AsyncSession, project_id: int) -> bool:
    """删除项目（级联删除相关测试记录）"""
    stmt = delete(Project).where(Project.id == project_id)
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount > 0


# ==================== 测试运行相关操作 ====================

async def create_test_run(
    session: AsyncSession,
    project_id: int,
    test_path: str,
    pytest_options: Optional[List[str]] = None,
    status: TestRunStatus = TestRunStatus.PENDING,
    start_time: Optional[datetime] = None,
) -> TestRun:
    """创建测试运行记录"""
    test_run = TestRun(
        project_id=project_id,
        test_path=test_path,
        pytest_options=pytest_options or [],
        status=status,
        start_time=start_time or datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    session.add(test_run)
    await session.commit()
    await session.refresh(test_run)
    
    return test_run


async def get_test_run(session: AsyncSession, run_id: int) -> Optional[TestRun]:
    """获取测试运行记录（包含关联数据）"""
    stmt = (
        select(TestRun)
        .where(TestRun.id == run_id)
        .options(
            selectinload(TestRun.test_cases),
            selectinload(TestRun.html_reports),
            selectinload(TestRun.test_analyses),
            selectinload(TestRun.project),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_test_runs(
    session: AsyncSession,
    project_id: Optional[int] = None,
    status: Optional[TestRunStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[TestRun]:
    """获取测试运行记录列表"""
    stmt = select(TestRun).options(selectinload(TestRun.project))
    
    # 添加过滤条件
    filters = []
    if project_id:
        filters.append(TestRun.project_id == project_id)
    if status:
        filters.append(TestRun.status == status)
    if start_date:
        filters.append(TestRun.created_at >= start_date)
    if end_date:
        filters.append(TestRun.created_at <= end_date)
    
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
    update_data = {}
    for key, value in kwargs.items():
        if hasattr(TestRun, key) and value is not None:
            update_data[key] = value
    
    if not update_data:
        return None
    
    # 如果是完成状态，设置结束时间
    if "status" in update_data and update_data["status"] in [
        TestRunStatus.COMPLETED, TestRunStatus.FAILED, TestRunStatus.CANCELLED
    ]:
        update_data["end_time"] = datetime.utcnow()
    
    # 更新更新时间
    update_data["updated_at"] = datetime.utcnow()
    
    stmt = (
        update(TestRun)
        .where(TestRun.id == run_id)
        .values(**update_data)
        .returning(TestRun)
    )
    
    result = await session.execute(stmt)
    await session.commit()
    
    return result.scalar_one_or_none()


async def update_test_run_results(
    session: AsyncSession,
    run_id: int,
    total_tests: int,
    passed: int,
    failed: int,
    skipped: int,
    error: int,
    duration: float,
    status: TestRunStatus = TestRunStatus.COMPLETED,
) -> Optional[TestRun]:
    """更新测试运行结果"""
    return await update_test_run(
        session=session,
        run_id=run_id,
        total_tests=total_tests,
        passed=passed,
        failed=failed,
        skipped=skipped,
        error=error,
        duration=duration,
        status=status,
        end_time=datetime.utcnow(),
    )


async def delete_test_run(session: AsyncSession, run_id: int) -> bool:
    """删除测试运行记录（级联删除相关数据）"""
    stmt = delete(TestRun).where(TestRun.id == run_id)
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount > 0


# ==================== 测试用例相关操作 ====================

async def create_test_case(
    session: AsyncSession,
    run_id: int,
    test_name: str,
    status: TestCaseStatus,
    duration: float = 0.0,
    test_file: Optional[str] = None,
    test_class: Optional[str] = None,
    test_method: Optional[str] = None,
    error_message: Optional[str] = None,
    stack_trace: Optional[str] = None,
    stdout: Optional[str] = None,
    stderr: Optional[str] = None,
) -> TestCase:
    """创建测试用例记录"""
    test_case = TestCase(
        run_id=run_id,
        test_name=test_name,
        test_file=test_file,
        test_class=test_class,
        test_method=test_method,
        status=status,
        duration=duration,
        error_message=error_message,
        stack_trace=stack_trace,
        stdout=stdout,
        stderr=stderr,
        created_at=datetime.utcnow(),
    )
    
    session.add(test_case)
    await session.commit()
    await session.refresh(test_case)
    
    return test_case


async def create_test_cases_batch(
    session: AsyncSession,
    test_cases: List[Dict[str, Any]],
) -> List[TestCase]:
    """批量创建测试用例记录"""
    case_objects = []
    for case_data in test_cases:
        case = TestCase(
            run_id=case_data["run_id"],
            test_name=case_data["test_name"],
            status=TestCaseStatus(case_data["status"]),
            duration=case_data.get("duration", 0.0),
            test_file=case_data.get("test_file"),
            test_class=case_data.get("test_class"),
            test_method=case_data.get("test_method"),
            error_message=case_data.get("error_message"),
            stack_trace=case_data.get("stack_trace"),
            stdout=case_data.get("stdout"),
            stderr=case_data.get("stderr"),
            created_at=datetime.utcnow(),
        )
        case_objects.append(case)
    
    session.add_all(case_objects)
    await session.commit()
    
    # 刷新所有对象以获取ID
    for case in case_objects:
        await session.refresh(case)
    
    return case_objects


async def get_test_cases_by_run(
    session: AsyncSession,
    run_id: int,
    status: Optional[TestCaseStatus] = None,
    limit: int = 1000,
    offset: int = 0,
) -> List[TestCase]:
    """获取测试运行的所有测试用例"""
    stmt = select(TestCase).where(TestCase.run_id == run_id)
    
    if status:
        stmt = stmt.where(TestCase.status == status)
    
    stmt = stmt.order_by(TestCase.id).limit(limit).offset(offset)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_test_cases_by_status(
    session: AsyncSession,
    project_id: int,
    status: TestCaseStatus,
    days: int = 7,
    limit: int = 100,
) -> List[TestCase]:
    """获取指定状态的测试用例"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    stmt = (
        select(TestCase)
        .join(TestRun, TestCase.run_id == TestRun.id)
        .where(
            and_(
                TestRun.project_id == project_id,
                TestCase.status == status,
                TestRun.created_at >= start_date,
            )
        )
        .order_by(TestRun.created_at.desc())
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ==================== HTML测试报告相关操作 ====================

async def create_html_report(
    session: AsyncSession,
    run_id: int,
    report_name: str,
    report_type: str = "pytest-html",
    file_path: Optional[str] = None,
    content: Optional[Union[bytes, str]] = None,
) -> HTMLReport:
    """创建HTML测试报告记录"""
    # 处理内容
    binary_content = None
    if content:
        if isinstance(content, str):
            binary_content = content.encode('utf-8')
        else:
            binary_content = content
    
    report = HTMLReport(
        run_id=run_id,
        report_name=report_name,
        report_type=report_type,
        file_path=file_path,
        content=binary_content,
        size=len(binary_content) if binary_content else 0,
        created_at=datetime.utcnow(),
    )
    
    session.add(report)
    await session.commit()
    await session.refresh(report)
    
    return report


async def get_html_report(session: AsyncSession, report_id: int) -> Optional[HTMLReport]:
    """获取HTML测试报告"""
    stmt = select(HTMLReport).where(HTMLReport.id == report_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_html_reports_by_run(
    session: AsyncSession,
    run_id: int,
    limit: int = 10,
) -> List[HTMLReport]:
    """获取测试运行的所有HTML报告"""
    stmt = (
        select(HTMLReport)
        .where(HTMLReport.run_id == run_id)
        .order_by(HTMLReport.created_at.desc())
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_html_report_content(
    session: AsyncSession,
    report_id: int,
    as_string: bool = True,
) -> Optional[Union[str, bytes]]:
    """获取HTML报告内容"""
    report = await get_html_report(session, report_id)
    if not report or not report.content:
        return None
    
    if as_string:
        return report.content.decode('utf-8')
    else:
        return report.content


# ==================== 测试分析相关操作 ====================

async def create_test_analysis(
    session: AsyncSession,
    run_id: int,
    analysis_type: str,
    metrics: Dict[str, Any],
    summary: Optional[str] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None,
) -> TestAnalysis:
    """创建测试分析结果"""
    analysis = TestAnalysis(
        run_id=run_id,
        analysis_type=analysis_type,
        metrics=metrics,
        summary=summary,
        recommendations=recommendations or [],
        created_at=datetime.utcnow(),
    )
    
    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)
    
    return analysis


async def get_test_analysis(session: AsyncSession, analysis_id: int) -> Optional[TestAnalysis]:
    """获取测试分析结果"""
    stmt = select(TestAnalysis).where(TestAnalysis.id == analysis_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_test_analyses_by_run(
    session: AsyncSession,
    run_id: int,
    analysis_type: Optional[str] = None,
    limit: int = 10,
) -> List[TestAnalysis]:
    """获取测试运行的所有分析结果"""
    stmt = select(TestAnalysis).where(TestAnalysis.run_id == run_id)
    
    if analysis_type:
        stmt = stmt.where(TestAnalysis.analysis_type == analysis_type)
    
    stmt = stmt.order_by(TestAnalysis.created_at.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ==================== 测试历史统计相关操作 ====================

async def create_test_history(
    session: AsyncSession,
    project_id: int,
    date: datetime,
    total_runs: int,
    total_tests: int,
    avg_success_rate: float,
    avg_duration: float,
    flaky_tests: Optional[List[Dict[str, Any]]] = None,
) -> TestHistory:
    """创建测试历史统计"""
    history = TestHistory(
        project_id=project_id,
        date=date,
        total_runs=total_runs,
        total_tests=total_tests,
        avg_success_rate=avg_success_rate,
        avg_duration=avg_duration,
        flaky_tests=flaky_tests or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    session.add(history)
    await session.commit()
    await session.refresh(history)
    
    return history


async def get_test_history_by_project(
    session: AsyncSession,
    project_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 30,
) -> List[TestHistory]:
    """获取项目的测试历史统计"""
    stmt = select(TestHistory).where(TestHistory.project_id == project_id)
    
    filters = []
    if start_date:
        filters.append(TestHistory.date >= start_date)
    if end_date:
        filters.append(TestHistory.date <= end_date)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    stmt = stmt.order_by(TestHistory.date.desc()).limit(limit)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ==================== 统计分析相关操作 ====================

async def get_project_statistics(
    session: AsyncSession,
    project_id: int,
    days: int = 30,
) -> Dict[str, Any]:
    """获取项目详细统计信息"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 查询测试运行统计
    stmt = select(
        func.count(TestRun.id).label("total_runs"),
        func.sum(TestRun.total_tests).label("total_tests"),
        func.sum(TestRun.passed).label("total_passed"),
        func.sum(TestRun.failed).label("total_failed"),
        func.sum(TestRun.skipped).label("total_skipped"),
        func.sum(TestRun.error).label("total_error"),
        func.avg(TestRun.duration).label("avg_duration"),
        func.max(TestRun.success_rate).label("max_success_rate"),
        func.min(TestRun.success_rate).label("min_success_rate"),
    ).where(
        and_(
            TestRun.project_id == project_id,
            TestRun.created_at >= start_date,
            TestRun.status == TestRunStatus.COMPLETED,
        )
    )
    
    result = await session.execute(stmt)
    stats = result.first()
    
    # 查询状态分布
    status_stmt = select(
        TestRun.status,
        func.count(TestRun.id).label("count")
    ).where(
        and_(
            TestRun.project_id == project_id,
            TestRun.created_at >= start_date,
        )
    ).group_by(TestRun.status)
    
    status_result = await session.execute(status_stmt)
    status_distribution = {row[0].value: row[1] for row in status_result}
    
    # 查询最近10次运行
    recent_stmt = (
        select(TestRun)
        .where(
            and_(
                TestRun.project_id == project_id,
                TestRun.created_at >= start_date,
            )
        )
        .order_by(TestRun.created_at.desc())
        .limit(10)
    )
    
    recent_result = await session.execute(recent_stmt)
    recent_runs = list(recent_result.scalars().all())
    
    # 计算趋势
    trend = "stable"
    if len(recent_runs) >= 3:
        success_rates = [run.success_rate for run in recent_runs[:3]]
        if success_rates[0] > success_rates[-1] + 5:
            trend = "improving"
        elif success_rates[0] < success_rates[-1] - 5:
            trend = "declining"
    
    return {
        "project_id": project_id,
        "period_days": days,
        "total_runs": stats.total_runs or 0,
        "total_tests": stats.total_tests or 0,
        "total_passed": stats.total_passed or 0,
        "total_failed": stats.total_failed or 0,
        "total_skipped": stats.total_skipped or 0,
        "total_error": stats.total_error or 0,
        "avg_duration": float(stats.avg_duration or 0),
        "max_success_rate": float(stats.max_success_rate or 0),
        "min_success_rate": float(stats.min_success_rate or 0),
        "avg_success_rate": (stats.total_passed / stats.total_tests * 100) if stats.total_tests and stats.total_tests > 0 else 0,
        "status_distribution": status_distribution,
        "trend": trend,
        "last_updated": datetime.utcnow().isoformat(),
    }


async def get_flaky_tests(
    session: AsyncSession,
    project_id: int,
    days: int = 30,
    threshold: float = 0.3,  # 失败率超过30%认为是flaky
    min_runs: int = 5,  # 最少运行次数
) -> List[Dict[str, Any]]:
    """识别不稳定的测试用例（flaky tests）"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 查询每个测试用例的运行情况
    stmt = select(
        TestCase.test_name,
        func.count(TestCase.id).label("total_runs"),
        func.sum(case((TestCase.status == TestCaseStatus.PASSED, 1), else_=0)).label("passed"),
        func.sum(case((TestCase.status == TestCaseStatus.FAILED, 1), else_=0)).label("failed"),
        func.sum(case((TestCase.status == TestCaseStatus.ERROR, 1), else_=0)).label("error"),
    ).join(TestRun, TestCase.run_id == TestRun.id).where(
        and_(
            TestRun.project_id == project_id,
            TestRun.created_at >= start_date,
            TestRun.status == TestRunStatus.COMPLETED,
        )
    ).group_by(TestCase.test_name).having(
        func.count(TestCase.id) >= min_runs
    )
    
    result = await session.execute(stmt)
    test_stats = result.fetchall()
    
    flaky_tests = []
    for row in test_stats:
        total = row.total_runs
        failed_rate = (row.failed + row.error) / total if total > 0 else 0
        
        if failed_rate >= threshold:
            flaky_tests.append({
                "test_name": row.test_name,
                "total_runs": total,
                "passed": row.passed,
                "failed": row.failed,
                "error": row.error,
                "failed_rate": failed_rate,
                "stability": "flaky" if failed_rate >= 0.5 else "unstable",
            })
    
    # 按失败率排序
    flaky_tests.sort(key=lambda x: x["failed_rate"], reverse=True)
    
    return flaky_tests


async def get_test_coverage(
    session: AsyncSession,
    project_id: int,
    days: int = 7,
) -> Dict[str, Any]:
    """获取测试覆盖率分析"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 查询测试用例总数
    total_stmt = select(func.count(func.distinct(TestCase.test_name))).join(
        TestRun, TestCase.run_id == TestRun.id
    ).where(
        and_(
            TestRun.project_id == project_id,
            TestRun.created_at >= start_date,
        )
    )
    
    total_result = await session.execute(total_stmt)
    total_tests = total_result.scalar() or 0
    
    # 查询最近运行的测试用例
    recent_stmt = select(
        TestCase.test_name,
        func.max(TestRun.created_at).label("last_run"),
        func.avg(TestCase.duration).label("avg_duration"),
    ).join(TestRun, TestCase.run_id == TestRun.id).where(
        and_(
            TestRun.project_id == project_id,
            TestRun.created_at >= start_date,
        )
    ).group_by(TestCase.test_name).order_by(func.max(TestRun.created_at).desc()).limit(100)
    
    recent_result = await session.execute(recent_stmt)
    recent_tests = [
        {
            "test_name": row.test_name,
            "last_run": row.last_run.isoformat() if row.last_run else None,
            "avg_duration": float(row.avg_duration or 0),
        }
        for row in recent_result
    ]
    
    return {
        "total_tests": total_tests,
        "recent_tests": recent_tests,
        "coverage_period_days": days,
        "analysis_date": datetime.utcnow().isoformat(),
    }