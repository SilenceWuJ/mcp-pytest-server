"""
pytest执行器
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .models import (
    TestResult,
    TestCaseResult,
    TestStatus,
    PytestConfig,
    ExecutionContext,
)
from .runner import run_pytest_tests
from ..database import Database, create_test_run, create_test_case, update_test_run


class PytestExecutor:
    """pytest执行器"""
    
    def __init__(self, database: Optional[Database] = None):
        self.database = database
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.running_tasks: Dict[int, asyncio.Task] = {}
    
    async def execute_tests(
        self,
        context: ExecutionContext,
        store_to_db: bool = True,
    ) -> TestResult:
        """
        执行测试
        
        Args:
            context: 执行上下文
            store_to_db: 是否存储到数据库
        
        Returns:
            TestResult: 测试结果
        """
        # 创建数据库记录
        db_run = None
        if store_to_db and self.database:
            async with self.database.get_session() as session:
                db_run = await create_test_run(
                    session=session,
                    project_name=context.project_name,
                    test_path=context.config.test_path,
                    pytest_options=context.config.options,
                    environment=context.config.environment,
                    metadata=context.metadata,
                )
                run_id = db_run.id
        else:
            run_id = None
        
        # 运行测试
        test_result = await run_pytest_tests(context, capture_output=True)
        
        # 更新数据库记录
        if store_to_db and self.database and db_run:
            async with self.database.get_session() as session:
                # 更新测试运行记录
                await update_test_run(
                    session=session,
                    run_id=run_id,
                    total_tests=test_result.total_tests,
                    passed=test_result.passed,
                    failed=test_result.failed,
                    skipped=test_result.skipped,
                    errors=test_result.errors,
                    duration=test_result.duration,
                    status=test_result.status,
                    completed_at=test_result.completed_at,
                )
                
                # 创建测试用例记录
                for test_case in test_result.test_cases:
                    await create_test_case(
                        session=session,
                        run_id=run_id,
                        test_name=test_case.test_name,
                        node_id=test_case.node_id,
                        status=test_case.status.value,
                        duration=test_case.duration,
                        error_message=test_case.error_message,
                        stack_trace=test_case.stack_trace,
                        stdout=test_case.stdout,
                        stderr=test_case.stderr,
                        metadata=test_case.metadata,
                    )
        
        # 设置数据库ID
        test_result.metadata["db_run_id"] = run_id
        
        return test_result
    
    async def execute_tests_async(
        self,
        context: ExecutionContext,
        store_to_db: bool = True,
    ) -> int:
        """
        异步执行测试（返回任务ID）
        
        Args:
            context: 执行上下文
            store_to_db: 是否存储到数据库
        
        Returns:
            int: 任务ID
        """
        # 创建数据库记录
        db_run = None
        if store_to_db and self.database:
            async with self.database.get_session() as session:
                db_run = await create_test_run(
                    session=session,
                    project_name=context.project_name,
                    test_path=context.config.test_path,
                    pytest_options=context.config.options,
                    environment=context.config.environment,
                    metadata=context.metadata,
                )
                run_id = db_run.id
        else:
            # 生成临时任务ID
            run_id = int(datetime.utcnow().timestamp() * 1000)
        
        # 创建异步任务
        task = asyncio.create_task(
            self._execute_task(run_id, context, store_to_db, db_run)
        )
        self.running_tasks[run_id] = task
        
        return run_id
    
    async def _execute_task(
        self,
        run_id: int,
        context: ExecutionContext,
        store_to_db: bool,
        db_run: Any,
    ):
        """执行任务"""
        try:
            # 运行测试
            test_result = await run_pytest_tests(context, capture_output=True)
            
            # 更新数据库记录
            if store_to_db and self.database and db_run:
                async with self.database.get_session() as session:
                    # 更新测试运行记录
                    await update_test_run(
                        session=session,
                        run_id=run_id,
                        total_tests=test_result.total_tests,
                        passed=test_result.passed,
                        failed=test_result.failed,
                        skipped=test_result.skipped,
                        errors=test_result.errors,
                        duration=test_result.duration,
                        status=test_result.status,
                        completed_at=test_result.completed_at,
                    )
                    
                    # 创建测试用例记录
                    for test_case in test_result.test_cases:
                        await create_test_case(
                            session=session,
                            run_id=run_id,
                            test_name=test_case.test_name,
                            node_id=test_case.node_id,
                            status=test_case.status.value,
                            duration=test_case.duration,
                            error_message=test_case.error_message,
                            stack_trace=test_case.stack_trace,
                            stdout=test_case.stdout,
                            stderr=test_case.stderr,
                            metadata=test_case.metadata,
                        )
            
        except Exception as e:
            # 记录错误
            if store_to_db and self.database and db_run:
                async with self.database.get_session() as session:
                    await update_test_run(
                        session=session,
                        run_id=run_id,
                        status="failed",
                        completed_at=datetime.utcnow(),
                    )
        
        finally:
            # 清理任务
            self.running_tasks.pop(run_id, None)
    
    async def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "running",
                "done": task.done(),
            }
        
        # 检查数据库中的记录
        if self.database:
            async with self.database.get_session() as session:
                from ..database import get_test_run
                db_run = await get_test_run(session, task_id)
                if db_run:
                    return {
                        "task_id": task_id,
                        "status": db_run.status,
                        "done": db_run.is_completed,
                        "result": db_run.to_dict(),
                    }
        
        return None
    
    async def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            
            # 更新数据库状态
            if self.database:
                async with self.database.get_session() as session:
                    await update_test_run(
                        session=session,
                        run_id=task_id,
                        status="cancelled",
                        completed_at=datetime.utcnow(),
                    )
            
            return True
        
        return False
    
    async def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取运行中的任务"""
        tasks = []
        for task_id, task in self.running_tasks.items():
            tasks.append({
                "task_id": task_id,
                "status": "running",
                "done": task.done(),
            })
        return tasks