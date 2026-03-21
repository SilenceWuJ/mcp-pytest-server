"""
MCP Pytest测试服务器主程序
"""
import argparse
import sys
from pathlib import Path

from .config import settings
from .database import Database
from .mcp.server import MCPServer


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="MCP Pytest测试服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=settings.host,
        help=f"服务器监听地址 (默认: {settings.host})",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"服务器监听端口 (默认: {settings.port})",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        default=settings.debug,
        help="启用调试模式",
    )
    
    parser.add_argument(
        "--database-url",
        type=str,
        default=settings.database_url,
        help=f"数据库连接URL (默认: {settings.database_url})",
    )
    
    parser.add_argument(
        "--no-database",
        action="store_true",
        help="不使用数据库",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"MCP Pytest Server {settings.mcp_server_version}",
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 更新配置
    settings.host = args.host
    settings.port = args.port
    settings.debug = args.debug
    
    if not args.no_database:
        settings.database_url = args.database_url
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                MCP Pytest测试服务器                      ║
    ║               版本: {settings.mcp_server_version:<15}          ║
    ╠══════════════════════════════════════════════════════════╣
    ║ 服务器: {settings.host}:{settings.port:<10}                    ║
    ║ 数据库: {settings.database_url if not args.no_database else '禁用':<30} ║
    ║ 调试模式: {str(settings.debug):<10}                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 初始化数据库
        database = None
        if not args.no_database:
            database = Database(settings.database_url)
            print(f"✓ 数据库已配置: {settings.database_url}")
        else:
            print("⚠ 数据库已禁用，测试结果将不会保存")
        
        # 创建MCP服务器
        server = MCPServer(database)
        
        print("\n可用端点:")
        print(f"  • MCP接口: http://{settings.host}:{settings.port}/mcp")
        print(f"  • 健康检查: http://{settings.host}:{settings.port}/health")
        print(f"  • 工具列表: http://{settings.host}:{settings.port}/tools")
        print(f"  • 资源列表: http://{settings.host}:{settings.port}/resources")
        print(f"  • 执行测试: http://{settings.host}:{settings.port}/execute")
        
        print("\n可用工具:")
        print("  • run_pytest_tests - 执行pytest测试")
        print("  • get_test_history - 获取测试历史记录")
        print("  • get_project_stats - 获取项目统计信息")
        print("  • get_test_run_details - 获取测试运行详情")
        
        print("\n" + "="*60)
        print("服务器正在启动... (按 Ctrl+C 停止)")
        print("="*60 + "\n")
        
        # 运行服务器
        server.run(host=settings.host, port=settings.port)
        
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        if settings.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()