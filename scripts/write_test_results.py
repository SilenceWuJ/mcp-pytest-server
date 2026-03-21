#!/usr/bin/env python3
"""
测试结果写入数据库示例
"""
import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime
import json

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

# 读取数据库配置
config_path = Path(__file__).parent.parent / "config" / "database.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# 获取SQLite URL
db_url = config['database']['sqlite']['url']
# 提取数据库文件路径
db_path = db_url.replace('sqlite:///', '')
print(f"数据库文件: {db_path}")


def create_test_run(project_name, test_path, test_results):
    """
    创建测试运行记录并写入数据库
    
    Args:
        project_name: 项目名称
        test_path: 测试路径
        test_results: 测试结果字典，包含：
            - total_tests: 总测试数
            - passed: 通过数
            - failed: 失败数
            - skipped: 跳过数
            - duration: 持续时间（秒）
            - status: 状态
            - test_cases: 测试用例列表
    """
    print(f"\n创建测试运行记录: {project_name}")
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 插入测试运行记录
        cursor.execute("""
            INSERT INTO test_runs 
            (project_name, test_path, total_tests, passed, failed, skipped, duration, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_name,
            test_path,
            test_results['total_tests'],
            test_results['passed'],
            test_results['failed'],
            test_results['skipped'],
            test_results['duration'],
            test_results['status'],
            datetime.now().isoformat()
        ))
        
        # 获取插入的run_id
        run_id = cursor.lastrowid
        print(f"  ✓ 测试运行记录创建成功, ID: {run_id}")
        
        # 2. 插入测试用例记录
        test_cases = test_results.get('test_cases', [])
        for i, test_case in enumerate(test_cases, 1):
            cursor.execute("""
                INSERT INTO test_cases 
                (run_id, test_name, status, duration, error_message, stack_trace, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                test_case['test_name'],
                test_case['status'],
                test_case.get('duration', 0.0),
                test_case.get('error_message'),
                test_case.get('stack_trace'),
                datetime.now().isoformat()
            ))
            print(f"  ✓ 测试用例 {i} 创建成功: {test_case['test_name']}")
        
        # 提交事务
        conn.commit()
        print(f"  ✓ 事务提交成功")
        
        # 3. 验证写入的数据
        print(f"\n验证写入的数据:")
        
        # 查询测试运行记录
        cursor.execute("SELECT * FROM test_runs WHERE id = ?", (run_id,))
        run_record = cursor.fetchone()
        if run_record:
            print(f"  测试运行记录:")
            print(f"    ID: {run_record[0]}")
            print(f"    项目: {run_record[1]}")
            print(f"    测试路径: {run_record[2]}")
            print(f"    总测试数: {run_record[3]}")
            print(f"    通过: {run_record[4]}, 失败: {run_record[5]}, 跳过: {run_record[6]}")
            print(f"    持续时间: {run_record[7]}秒")
            print(f"    状态: {run_record[8]}")
            print(f"    创建时间: {run_record[9]}")
        
        # 查询测试用例记录
        cursor.execute("SELECT COUNT(*) FROM test_cases WHERE run_id = ?", (run_id,))
        case_count = cursor.fetchone()[0]
        print(f"  关联测试用例数: {case_count}")
        
        if case_count > 0:
            cursor.execute("SELECT test_name, status, duration FROM test_cases WHERE run_id = ?", (run_id,))
            cases = cursor.fetchall()
            print(f"  测试用例详情:")
            for case in cases:
                print(f"    - {case[0]}: {case[1]} ({case[2]}秒)")
        
        conn.close()
        print(f"\n✓ 测试结果写入完成!")
        return run_id
        
    except Exception as e:
        print(f"✗ 写入测试结果失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def query_test_results(project_name=None, limit=10):
    """
    查询测试结果
    
    Args:
        project_name: 项目名称（可选）
        limit: 返回结果数量限制
    """
    print(f"\n查询测试结果...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if project_name:
            cursor.execute("""
                SELECT * FROM test_runs 
                WHERE project_name = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (project_name, limit))
        else:
            cursor.execute("""
                SELECT * FROM test_runs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        
        runs = cursor.fetchall()
        
        print(f"找到 {len(runs)} 条测试运行记录:")
        for run in runs:
            print(f"\n  ID: {run[0]}")
            print(f"  项目: {run[1]}")
            print(f"  状态: {run[8]}")
            print(f"  测试数: {run[3]} (通过: {run[4]}, 失败: {run[5]}, 跳过: {run[6]})")
            print(f"  持续时间: {run[7]}秒")
            print(f"  创建时间: {run[9]}")
            
            # 查询关联的测试用例
            cursor.execute("""
                SELECT COUNT(*), 
                       SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed,
                       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                       SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
                FROM test_cases 
                WHERE run_id = ?
            """, (run[0],))
            
            case_stats = cursor.fetchone()
            print(f"  测试用例统计: 总数={case_stats[0]}, 通过={case_stats[1]}, 失败={case_stats[2]}, 跳过={case_stats[3]}")
        
        conn.close()
        return runs
        
    except Exception as e:
        print(f"✗ 查询测试结果失败: {e}")
        return []


def generate_sample_test_results():
    """生成示例测试结果"""
    return {
        'total_tests': 5,
        'passed': 3,
        'failed': 1,
        'skipped': 1,
        'duration': 12.5,
        'status': 'completed',
        'test_cases': [
            {
                'test_name': 'test_user_authentication',
                'status': 'passed',
                'duration': 2.5,
                'error_message': None,
                'stack_trace': None
            },
            {
                'test_name': 'test_user_registration',
                'status': 'passed',
                'duration': 3.0,
                'error_message': None,
                'stack_trace': None
            },
            {
                'test_name': 'test_password_reset',
                'status': 'failed',
                'duration': 4.0,
                'error_message': 'TimeoutError: Request timed out',
                'stack_trace': 'Traceback (most recent call last):\n  File "test_auth.py", line 45, in test_password_reset\n    response = client.post(...)\nTimeoutError: Request timed out'
            },
            {
                'test_name': 'test_user_profile',
                'status': 'passed',
                'duration': 2.0,
                'error_message': None,
                'stack_trace': None
            },
            {
                'test_name': 'test_admin_permissions',
                'status': 'skipped',
                'duration': 1.0,
                'error_message': 'Test requires admin privileges',
                'stack_trace': None
            }
        ]
    }


def main():
    """主函数"""
    print("=" * 60)
    print("测试结果写入数据库示例")
    print("=" * 60)
    
    # 1. 生成示例测试结果
    print("\n1. 生成示例测试结果...")
    sample_results = generate_sample_test_results()
    print(f"   总测试数: {sample_results['total_tests']}")
    print(f"   通过: {sample_results['passed']}, 失败: {sample_results['failed']}, 跳过: {sample_results['skipped']}")
    print(f"   持续时间: {sample_results['duration']}秒")
    print(f"   状态: {sample_results['status']}")
    print(f"   测试用例数: {len(sample_results['test_cases'])}")
    
    # 2. 写入数据库
    print("\n2. 写入数据库...")
    run_id = create_test_run(
        project_name="auth_service",
        test_path="tests/test_auth.py",
        test_results=sample_results
    )
    
    if not run_id:
        print("✗ 写入失败，退出")
        return
    
    # 3. 查询验证
    print("\n3. 查询验证...")
    query_test_results(project_name="auth_service")
    
    # 4. 查询所有项目
    print("\n4. 查询所有项目测试结果...")
    query_test_results(limit=5)
    
    print("\n" + "=" * 60)
    print("✓ 数据写入功能验证完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()