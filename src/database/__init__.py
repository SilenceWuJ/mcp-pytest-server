"""
数据库模块
"""
from .models import Base, TestRun, TestCase
from .connection import Database,init_database,close_database
from .crud import (
    create_test_run,
    get_test_run,
    get_test_runs,
    update_test_run,
    delete_test_run,
    create_test_case,
    get_test_cases_by_run,
    get_test_history,
    get_project_stats,
)

__all__ = [
    "Base",
    "TestRun",
    "TestCase",
    "Database",
    "create_test_run",
    "get_test_run",
    "get_test_runs",
    "update_test_run",
    "delete_test_run",
    "create_test_case",
    "get_test_cases_by_run",
    "get_test_history",
    "get_project_stats",
]