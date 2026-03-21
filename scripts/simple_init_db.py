# #!/usr/bin/env python3
# """
# 简单的数据库初始化脚本
# """
# import sys
# import os
# from pathlib import Path
#
# # 添加项目根目录到Python路径
# sys.path.insert(0, str(Path(__file__).parent.parent))
#
# import yaml
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import sessionmaker
#
# # 读取数据库配置
# config_path = Path(__file__).parent.parent / "config" / "database.yaml"
# with open(config_path, 'r') as f:
#     config = yaml.safe_load(f)
#
# # 获取SQLite URL
# db_url = config['database']['sqlite']['url']
# print(f"数据库URL: {db_url}")
#
# # 创建同步引擎（SQLAlchemy 1.4兼容）
# engine = create_engine(db_url, echo=True)
#
# # 创建表SQL语句
# create_tables_sql = """
# -- 创建 test_runs 表
# CREATE TABLE IF NOT EXISTS test_runs (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     project_name TEXT NOT NULL,
#     test_path TEXT NOT NULL,
#     total_tests INTEGER,
#     passed INTEGER,
#     failed INTEGER,
#     skipped INTEGER,
#     duration REAL,
#     status TEXT,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );
#
# -- 创建 test_cases 表
# CREATE TABLE IF NOT EXISTS test_cases (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     run_id INTEGER,
#     test_name TEXT NOT NULL,
#     status TEXT,
#     duration REAL,
#     error_message TEXT,
#     stack_trace TEXT,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (run_id) REFERENCES test_runs (id) ON DELETE CASCADE
# );
#
# -- 创建索引
# CREATE INDEX IF NOT EXISTS idx_test_runs_project_name ON test_runs(project_name);
# CREATE INDEX IF NOT EXISTS idx_test_runs_created_at ON test_runs(created_at);
# CREATE INDEX IF NOT EXISTS idx_test_cases_run_id ON test_cases(run_id);
# CREATE INDEX IF NOT EXISTS idx_test_cases_test_name ON test_cases(test_name);
# """
#
# # 插入示例数据的SQL
# sample_data_sql = """
# -- 插入示例测试运行数据
# INSERT OR IGNORE INTO test_runs
# (project_name, test_path, total_tests, passed, failed, skipped, duration, status, created_at)
# VALUES
# ('example_project', 'tests/test_example.py', 10, 8, 1, 1, 5.5, 'completed', datetime('now', '-1 day')),
# ('demo_project', 'tests/demo_test.py', 15, 14, 0, 1, 8.2, 'completed', datetime('now', '-2 hours'));
#
# -- 插入示例测试用例数据
# INSERT OR IGNORE INTO test_cases
# (run_id, test_name, status, duration, error_message, stack_trace, created_at)
# VALUES
# (1, 'test_example_1', 'passed', 0.5, NULL, NULL, datetime('now', '-1 day')),
# (1, 'test_example_2', 'passed', 0.6, NULL, NULL, datetime('now', '-1 day')),
# (1, 'test_example_3', 'failed', 0.7, 'AssertionError: Expected 2 but got 3', 'Traceback...', datetime('now', '-1 day')),
# (1, 'test_example_4', 'skipped', 0.0, NULL, NULL, datetime('now', '-1 day')),
# (2, 'test_demo_1', 'passed', 0.8, NULL, NULL, datetime('now', '-2 hours')),
# (2, 'test_demo_2', 'passed', 0.9, NULL, NULL, datetime('now', '-2 hours'));
# """
#
# def init_database():
#     """初始化数据库"""
#     print("正在初始化数据库...")
#
#     try:
#         # 创建连接
#         with engine.begin() as conn:
#             # 执行创建表语句（逐条执行）
#             print("创建表...")
#             statements = create_tables_sql.strip().split(';')
#             for stmt in statements:
#                 stmt = stmt.strip()
#                 if stmt:
#                     conn.execute(text(stmt + ';'))
#
#             # 检查表是否创建成功
#             result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
#             tables = result.fetchall()
#
#             print("\n已创建的表:")
#             for table in tables:
#                 print(f"  - {table[0]}")
#
#                 # 显示表结构
#                 result2 = conn.execute(text(f"PRAGMA table_info({table[0]});"))
#                 columns = result2.fetchall()
#                 for col in columns:
#                     not_null = " NOT NULL" if col[3] else ""
#                     pk = " PRIMARY KEY" if col[5] else ""
#                     print(f"    * {col[1]} ({col[2]}{not_null}{pk})")
#
#             # 插入示例数据（逐条执行）
#             print("\n插入示例数据...")
#             statements = sample_data_sql.strip().split(';')
#             for stmt in statements:
#                 stmt = stmt.strip()
#                 if stmt:
#                     conn.execute(text(stmt + ';'))
#
#             # 验证数据
#             print("\n验证数据:")
#
#             # 统计test_runs表数据
#             result = conn.execute(text("SELECT COUNT(*) FROM test_runs;"))
#             run_count = result.fetchone()[0]
#             print(f"  test_runs表: {run_count} 条记录")
#
#             # 统计test_cases表数据
#             result = conn.execute(text("SELECT COUNT(*) FROM test_cases;"))
#             case_count = result.fetchone()[0]
#             print(f"  test_cases表: {case_count} 条记录")
#
#             # 显示测试运行统计
#             result = conn.execute(text("""
#                 SELECT
#                     project_name,
#                     COUNT(*) as run_count,
#                     SUM(total_tests) as total_tests,
#                     SUM(passed) as total_passed,
#                     SUM(failed) as total_failed,
#                     SUM(skipped) as total_skipped
#                 FROM test_runs
#                 GROUP BY project_name;
#             """))
#
#             print("\n项目统计:")
#             for row in result.fetchall():
#                 success_rate = (row[3] / row[2] * 100) if row[2] > 0 else 0
#                 print(f"  {row[0]}: {row[1]}次运行, {row[2]}个测试, 通过率: {success_rate:.1f}%")
#
#             print("\n✓ 数据库初始化完成!")
#
#     except Exception as e:
#         print(f"✗ 数据库初始化失败: {e}")
#         import traceback
#         traceback.print_exc()
#         return False
#
#     return True
#
#
# def check_database():
#     """检查数据库状态"""
#     print("检查数据库状态...")
#
#     try:
#         with engine.begin() as conn:
#             # 检查表是否存在
#             result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"))
#             tables = result.fetchall()
#
#             if tables:
#                 print("\n现有表:")
#                 for table in tables:
#                     print(f"  - {table[0]}")
#
#                     # 显示表数据量
#                     result2 = conn.execute(text(f"SELECT COUNT(*) FROM {table[0]};"))
#                     count = result2.fetchone()[0]
#                     print(f"    记录数: {count}")
#             else:
#                 print("数据库中没有表")
#
#     except Exception as e:
#         print(f"检查数据库失败: {e}")
#         return False
#
#     return True
#
#
# def clear_database():
#     """清空数据库"""
#     confirm = input("确认清空所有数据? (yes/no): ")
#     if confirm.lower() != "yes":
#         print("操作取消")
#         return False
#
#     print("清空数据库...")
#
#     try:
#         with engine.begin() as conn:
#             # 删除所有表（注意：这会删除所有数据！）
#             conn.execute(text("DROP TABLE IF EXISTS test_cases;"))
#             conn.execute(text("DROP TABLE IF EXISTS test_runs;"))
#             conn.commit()
#             print("✓ 数据库已清空")
#
#     except Exception as e:
#         print(f"✗ 清空数据库失败: {e}")
#         return False
#
#     return True
#
#
# if __name__ == "__main__":
#     import argparse
#
#     parser = argparse.ArgumentParser(description="数据库管理工具")
#     parser.add_argument("action", choices=["init", "check", "clear"],
#                        help="操作: init-初始化, check-检查状态, clear-清空数据")
#
#     args = parser.parse_args()
#
#     if args.action == "init":
#         init_database()
#     elif args.action == "check":
#         check_database()
#     elif args.action == "clear":
#         clear_database()


# !/usr/bin/env python3
"""
简单的数据库初始化脚本 (MySQL 版本)
用于创建 MCP 服务器所需的表，表名加前缀 mcp_ 以避免与 QA 平台冲突
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from sqlalchemy import create_engine, text

# ===== 数据库配置 =====
# 直接从参数或环境变量读取，这里直接使用 QA 平台的 MySQL 配置
DB_USER = 'qa_user'
DB_PASSWORD = '123456'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'qa_platform'

# 构造 MySQL 连接 URL（同步驱动使用 pymysql）
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

print(f"数据库URL: {DB_URL}")

# 创建同步引擎
engine = create_engine(DB_URL, echo=True, pool_pre_ping=True)

# ===== 创建表的 SQL（MySQL 语法，表名加前缀 mcp_） =====
create_tables_sql = f"""
-- 创建 test_runs 表
CREATE TABLE IF NOT EXISTS mcp_test_runs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_name VARCHAR(255) NOT NULL,
    test_path VARCHAR(500) NOT NULL,
    total_tests INT,
    passed INT,
    failed INT,
    skipped INT,
    duration FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建 test_cases 表
CREATE TABLE IF NOT EXISTS mcp_test_cases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    run_id INT NOT NULL,
    test_name VARCHAR(500) NOT NULL,
    status VARCHAR(50),
    duration FLOAT,
    error_message TEXT,
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES mcp_test_runs (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_mcp_test_runs_project_name ON mcp_test_runs(project_name);
CREATE INDEX IF NOT EXISTS idx_mcp_test_runs_created_at ON mcp_test_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_mcp_test_cases_run_id ON mcp_test_cases(run_id);
CREATE INDEX IF NOT EXISTS idx_mcp_test_cases_test_name ON mcp_test_cases(test_name);
"""

# 插入示例数据的SQL（MySQL 语法）
sample_data_sql = f"""
-- 插入示例测试运行数据
INSERT INTO mcp_test_runs 
(project_name, test_path, total_tests, passed, failed, skipped, duration, status, created_at)
VALUES 
('example_project', 'tests/test_example.py', 10, 8, 1, 1, 5.5, 'completed', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('demo_project', 'tests/demo_test.py', 15, 14, 0, 1, 8.2, 'completed', DATE_SUB(NOW(), INTERVAL 2 HOUR))
ON DUPLICATE KEY UPDATE id=id;

-- 插入示例测试用例数据
INSERT INTO mcp_test_cases 
(run_id, test_name, status, duration, error_message, stack_trace, created_at)
VALUES 
(1, 'test_example_1', 'passed', 0.5, NULL, NULL, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(1, 'test_example_2', 'passed', 0.6, NULL, NULL, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(1, 'test_example_3', 'failed', 0.7, 'AssertionError: Expected 2 but got 3', 'Traceback...', DATE_SUB(NOW(), INTERVAL 1 DAY)),
(1, 'test_example_4', 'skipped', 0.0, NULL, NULL, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(2, 'test_demo_1', 'passed', 0.8, NULL, NULL, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(2, 'test_demo_2', 'passed', 0.9, NULL, NULL, DATE_SUB(NOW(), INTERVAL 2 HOUR))
ON DUPLICATE KEY UPDATE id=id;
"""


def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")

    try:
        with engine.begin() as conn:
            # 执行创建表语句（逐条执行）
            print("创建表...")
            statements = create_tables_sql.strip().split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt + ';'))

            # 检查表是否创建成功
            result = conn.execute(text("SHOW TABLES LIKE 'mcp_%';"))
            tables = [row[0] for row in result.fetchall()]

            print("\n已创建的表:")
            for table in sorted(tables):
                print(f"  - {table}")

                # 显示表结构
                result2 = conn.execute(text(f"DESCRIBE {table};"))
                columns = result2.fetchall()
                for col in columns:
                    print(f"    * {col[0]} ({col[1]})")

            # 插入示例数据（逐条执行）
            print("\n插入示例数据...")
            statements = sample_data_sql.strip().split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt + ';'))

            # 验证数据
            print("\n验证数据:")

            # 统计 mcp_test_runs 表数据
            result = conn.execute(text("SELECT COUNT(*) FROM mcp_test_runs;"))
            run_count = result.fetchone()[0]
            print(f"  mcp_test_runs 表: {run_count} 条记录")

            # 统计 mcp_test_cases 表数据
            result = conn.execute(text("SELECT COUNT(*) FROM mcp_test_cases;"))
            case_count = result.fetchone()[0]
            print(f"  mcp_test_cases 表: {case_count} 条记录")

            # 显示测试运行统计
            result = conn.execute(text("""
                                       SELECT project_name,
                                              COUNT(*)         as run_count,
                                              SUM(total_tests) as total_tests,
                                              SUM(passed)      as total_passed,
                                              SUM(failed)      as total_failed,
                                              SUM(skipped)     as total_skipped
                                       FROM mcp_test_runs
                                       GROUP BY project_name;
                                       """))

            print("\n项目统计:")
            for row in result.fetchall():
                success_rate = (row[3] / row[2] * 100) if row[2] > 0 else 0
                print(f"  {row[0]}: {row[1]}次运行, {row[2]}个测试, 通过率: {success_rate:.1f}%")

            print("\n✓ 数据库初始化完成!")

    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def check_database():
    """检查数据库状态"""
    print("检查数据库状态...")

    try:
        with engine.begin() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'mcp_%';"))
            tables = [row[0] for row in result.fetchall()]

            if tables:
                print("\n现有表:")
                for table in tables:
                    print(f"  - {table}")
                    # 显示表数据量
                    result2 = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count = result2.fetchone()[0]
                    print(f"    记录数: {count}")
            else:
                print("数据库中没有 mcp_ 前缀的表")

    except Exception as e:
        print(f"检查数据库失败: {e}")
        return False

    return True


def clear_database():
    """清空数据库（删除 mcp_ 前缀的表）"""
    confirm = input("确认清空所有 MCP 相关数据? (yes/no): ")
    if confirm.lower() != "yes":
        print("操作取消")
        return False

    print("清空数据库...")

    try:
        with engine.begin() as conn:
            # 获取所有 mcp_ 前缀的表
            result = conn.execute(text("SHOW TABLES LIKE 'mcp_%';"))
            tables = [row[0] for row in result.fetchall()]
            for table in tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table};"))
            print(f"✓ 已删除 {len(tables)} 张表")

    except Exception as e:
        print(f"✗ 清空数据库失败: {e}")
        return False

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库管理工具 (MySQL)")
    parser.add_argument("action", choices=["init", "check", "clear"],
                        help="操作: init-初始化, check-检查状态, clear-清空数据")

    args = parser.parse_args()

    if args.action == "init":
        init_database()
    elif args.action == "check":
        check_database()
    elif args.action == "clear":
        clear_database()