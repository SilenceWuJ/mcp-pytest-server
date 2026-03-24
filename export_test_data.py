#!/usr/bin/env python3
"""
测试数据导出工具
将数据库中的测试数据导出为JSON或CSV格式
"""
import asyncio
import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# 数据库连接配置
DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/qa_platform"

class TestDataExporter:
    """测试数据导出类"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def connect(self):
        """连接数据库"""
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            await self.engine.dispose()
    
    async def export_all_data(self, format: str = "json") -> Dict[str, Any]:
        """导出所有数据"""
        async with self.async_session() as session:
            data = {}
            
            # 1. 导出项目
            result = await session.execute(
                text("SELECT * FROM projects ORDER BY id")
            )
            projects = []
            for row in result.fetchall():
                project = {
                    'id': row[0],
                    'name': row[1],
                    'start_date': row[2].isoformat() if row[2] else None,
                    'end_date': row[3].isoformat() if row[3] else None,
                    'progress': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                }
                projects.append(project)
            data['projects'] = projects
            
            # 2. 导出测试用例
            result = await session.execute(
                text("""
                SELECT 
                    tc.*,
                    p.name as project_name,
                    tp.name as test_phase_name,
                    tt.name as test_type_name,
                    m.name as mark_name
                FROM testcases tc
                LEFT JOIN projects p ON tc.project_id = p.id
                LEFT JOIN test_phases tp ON tc.test_phase_id = tp.id
                LEFT JOIN test_types tt ON tc.test_type_id = tt.id
                LEFT JOIN marks m ON tc.mark_id = m.id
                ORDER BY tc.id
                """)
            )
            testcases = []
            for row in result.fetchall():
                testcase = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'steps': row[3],
                    'expected_result': row[4],
                    'project_id': row[5],
                    'project_name': row[17],
                    'requirement_id': row[6],
                    'test_phase_id': row[7],
                    'test_phase_name': row[18],
                    'test_type_id': row[8],
                    'test_type_name': row[19],
                    'mark_id': row[9],
                    'mark_name': row[20],
                    'latest_result_id': row[10],
                    'is_deleted': bool(row[11]) if row[11] is not None else None,
                    'created_at': row[12].isoformat() if row[12] else None,
                    'updated_at': row[13].isoformat() if row[13] else None,
                    'test_script': row[14]
                }
                testcases.append(testcase)
            data['testcases'] = testcases
            
            # 3. 导出测试执行记录
            result = await session.execute(
                text("SELECT * FROM mcp_test_runs ORDER BY id")
            )
            test_runs = []
            for row in result.fetchall():
                test_run = {
                    'id': row[0],
                    'project_name': row[1],
                    'test_path': row[2],
                    'total_tests': row[3],
                    'passed': row[4],
                    'failed': row[5],
                    'skipped': row[6],
                    'duration': float(row[7]) if row[7] else None,
                    'status': row[8],
                    'created_at': row[9].isoformat() if row[9] else None
                }
                test_runs.append(test_run)
            data['test_runs'] = test_runs
            
            # 4. 导出测试报告
            result = await session.execute(
                text("""
                SELECT 
                    tr.*,
                    tc.name as testcase_name
                FROM test_reports tr
                LEFT JOIN testcases tc ON tr.testcase_id = tc.id
                ORDER BY tr.id
                """)
            )
            test_reports = []
            for row in result.fetchall():
                test_report = {
                    'id': row[0],
                    'testcase_id': row[1],
                    'testcase_name': row[7],
                    'status': row[2],
                    'result': row[3],
                    'started_at': row[4].isoformat() if row[4] else None,
                    'finished_at': row[5].isoformat() if row[5] else None,
                    'log': row[6]
                }
                test_reports.append(test_report)
            data['test_reports'] = test_reports
            
            # 5. 导出HTML报告
            result = await session.execute(
                text("SELECT * FROM reports ORDER BY id")
            )
            html_reports = []
            for row in result.fetchall():
                html_report = {
                    'html_content': row[0],
                    'id': row[1],
                    'execution_id': row[2],
                    'content': row[3],
                    'created_at': row[4].isoformat() if row[4] else None
                }
                html_reports.append(html_report)
            data['html_reports'] = html_reports
            
            # 6. 导出文件记录
            result = await session.execute(
                text("SELECT * FROM files ORDER BY id")
            )
            files = []
            for row in result.fetchall():
                file_record = {
                    'id': row[0],
                    'filename': row[1],
                    'original_filename': row[2],
                    'file_path': row[3],
                    'file_size': row[4],
                    'mime_type': row[5],
                    'uploaded_at': row[6].isoformat() if row[6] else None,
                    'uploader_id': row[7]
                }
                files.append(file_record)
            data['files'] = files
            
            # 7. 导出关联关系
            result = await session.execute(
                text("""
                SELECT 
                    tf.*,
                    tc.name as testcase_name,
                    f.filename as filename
                FROM testcase_files tf
                LEFT JOIN testcases tc ON tf.testcase_id = tc.id
                LEFT JOIN files f ON tf.file_id = f.id
                ORDER BY tf.testcase_id, tf.file_id
                """)
            )
            associations = []
            for row in result.fetchall():
                association = {
                    'testcase_id': row[0],
                    'file_id': row[1],
                    'testcase_name': row[2],
                    'filename': row[3]
                }
                associations.append(association)
            data['testcase_files'] = associations
            
            # 添加元数据
            data['metadata'] = {
                'export_time': datetime.now().isoformat(),
                'database': 'qa_platform',
                'total_records': {
                    'projects': len(projects),
                    'testcases': len(testcases),
                    'test_runs': len(test_runs),
                    'test_reports': len(test_reports),
                    'html_reports': len(html_reports),
                    'files': len(files),
                    'testcase_files': len(associations)
                }
            }
            
            return data
    
    async def export_to_json(self, filename: str = None):
        """导出为JSON文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_data_export_{timestamp}.json"
        
        print(f"正在导出数据到JSON文件: {filename}")
        
        data = await self.export_all_data()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据已导出到: {filename}")
        print(f"   总记录数: {data['metadata']['total_records']}")
        
        return filename
    
    async def export_to_csv(self, output_dir: str = "csv_export"):
        """导出为CSV文件"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"正在导出数据到CSV目录: {output_dir}")
        
        data = await self.export_all_data()
        
        # 导出每个表为单独的CSV文件
        for table_name, records in data.items():
            if table_name == 'metadata':
                continue
            
            if records:
                filename = os.path.join(output_dir, f"{table_name}.csv")
                
                # 获取所有可能的字段
                all_fields = set()
                for record in records:
                    all_fields.update(record.keys())
                
                fields = sorted(all_fields)
                
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(records)
                
                print(f"  ✅ {table_name}: {len(records)} 条记录 -> {filename}")
        
        # 导出元数据
        metadata_file = os.path.join(output_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data['metadata'], f, ensure_ascii=False, indent=2)
        
        print(f"✅ 所有数据已导出到目录: {output_dir}")
        print(f"   总记录数: {data['metadata']['total_records']}")
        
        return output_dir
    
    async def export_summary_report(self, filename: str = None):
        """导出摘要报告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_summary_{timestamp}.md"
        
        print(f"正在生成摘要报告: {filename}")
        
        async with self.async_session() as session:
            # 获取统计数据
            stats = {}
            tables = ['projects', 'testcases', 'mcp_test_runs', 'test_reports', 'reports', 'files']
            
            for table in tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                stats[table] = result.scalar()
            
            # 获取测试报告状态统计
            result = await session.execute(
                text("SELECT status, COUNT(*) FROM test_reports GROUP BY status")
            )
            report_stats = {row[0]: row[1] for row in result.fetchall()}
            
            # 获取最近的项目
            result = await session.execute(
                text("SELECT name, progress, created_at FROM projects ORDER BY created_at DESC LIMIT 3")
            )
            recent_projects = result.fetchall()
            
            # 获取测试成功率
            result = await session.execute(
                text("""
                SELECT 
                    AVG(passed * 100.0 / NULLIF(total_tests, 0)) as avg_success_rate,
                    SUM(total_tests) as total_tests,
                    SUM(passed) as total_passed,
                    SUM(failed) as total_failed
                FROM mcp_test_runs
                WHERE total_tests > 0
                """)
            )
            test_stats = result.fetchone()
            
            # 生成Markdown报告
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# QA测试平台数据摘要报告\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## 📊 数据统计\n\n")
                f.write("| 表名 | 记录数 |\n")
                f.write("|------|--------|\n")
                for table, count in stats.items():
                    f.write(f"| {table} | {count} |\n")
                
                f.write("\n## 📈 测试执行统计\n\n")
                if test_stats and test_stats[0]:
                    f.write(f"- 平均成功率: {test_stats[0]:.2f}%\n")
                    f.write(f"- 总测试用例数: {test_stats[1]}\n")
                    f.write(f"- 总通过数: {test_stats[2]}\n")
                    f.write(f"- 总失败数: {test_stats[3]}\n")
                
                f.write("\n## 📋 测试报告状态\n\n")
                for status, count in report_stats.items():
                    f.write(f"- {status}: {count}\n")
                
                f.write("\n## 🏢 最近项目\n\n")
                for project in recent_projects:
                    f.write(f"- **{project[0]}**\n")
                    f.write(f"  - 进度: {project[1]}%\n")
                    f.write(f"  - 创建时间: {project[2].strftime('%Y-%m-%d')}\n")
                
                f.write("\n## 🔗 数据文件\n\n")
                f.write("完整数据可通过以下方式导出:\n")
                f.write("- JSON格式: `python3 export_test_data.py --format json`\n")
                f.write("- CSV格式: `python3 export_test_data.py --format csv`\n")
        
        print(f"✅ 摘要报告已生成: {filename}")
        return filename

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试数据导出工具")
    parser.add_argument("--format", choices=["json", "csv", "summary"], default="json",
                       help="导出格式: json, csv, 或 summary")
    parser.add_argument("--output", help="输出文件或目录")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("测试数据导出工具")
    print("=" * 60)
    
    exporter = TestDataExporter()
    
    try:
        await exporter.connect()
        print("✅ 数据库连接成功")
        
        if args.format == "json":
            filename = args.output or None
            await exporter.export_to_json(filename)
        
        elif args.format == "csv":
            output_dir = args.output or "csv_export"
            await exporter.export_to_csv(output_dir)
        
        elif args.format == "summary":
            filename = args.output or None
            await exporter.export_summary_report(filename)
        
        print("\n" + "=" * 60)
        print("✅ 导出完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await exporter.disconnect()

if __name__ == "__main__":
    asyncio.run(main())