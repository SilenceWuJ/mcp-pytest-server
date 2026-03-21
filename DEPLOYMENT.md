# MCP Pytest 测试服务器部署指南

本文档提供 MCP Pytest 测试服务器的完整部署和配置指南。

## 1. 环境要求

### 1.1 系统要求
- **操作系统**: macOS, Linux, Windows (WSL2 推荐)
- **Python**: 3.8 或更高版本
- **内存**: 至少 2GB RAM
- **磁盘空间**: 至少 100MB 可用空间

### 1.2 软件依赖
- Python 3.8+
- pip (Python 包管理器)
- 虚拟环境工具 (venv 或 conda)
- Git (可选，用于版本控制)

## 2. 快速开始

### 2.1 克隆项目
```bash
# 克隆项目
git clone <repository-url>
cd mcp-pytest-server

# 或者直接使用现有目录
cd /path/to/mcp-pytest-server
```

### 2.2 使用启动脚本（推荐）
```bash
# 给启动脚本执行权限
chmod +x start.sh

# 初始化环境
./start.sh init

# 启动服务器
./start.sh start

# 或者指定参数启动
./start.sh start localhost 8080 true
```

### 2.3 手动安装
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 启动服务器
python -m src.main
```

## 3. 配置说明

### 3.1 环境变量配置
复制示例环境文件并修改：
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# 服务器配置
MCP_PYTEST_HOST=0.0.0.0
MCP_PYTEST_PORT=8000
MCP_PYTEST_DEBUG=false

# 数据库配置
MCP_PYTEST_DATABASE_URL=sqlite:///./test_results.db

# MCP配置
MCP_PYTEST_MCP_SERVER_NAME=pytest-test-server
MCP_PYTEST_MCP_SERVER_VERSION=0.1.0

# pytest配置
MCP_PYTEST_PYTEST_DEFAULT_OPTIONS=["-v", "--tb=short"]

# 日志配置
MCP_PYTEST_LOG_LEVEL=INFO
MCP_PYTEST_LOG_FILE=./logs/server.log
```

### 3.2 命令行参数
服务器支持以下命令行参数：
```bash
python -m src.main --help

# 常用参数
python -m src.main \
  --host 0.0.0.0 \
  --port 8080 \
  --debug \
  --database-url sqlite:///./test_results.db \
  --no-database  # 禁用数据库
```

## 4. 数据库配置

### 4.1 SQLite（默认）
```env
MCP_PYTEST_DATABASE_URL=sqlite:///./test_results.db
```

### 4.2 PostgreSQL
```env
MCP_PYTEST_DATABASE_URL=postgresql://user:password@localhost:5432/test_db
```

### 4.3 MySQL
```env
MCP_PYTEST_DATABASE_URL=mysql://user:password@localhost:3306/test_db
```

### 4.4 数据库初始化
```bash
# 使用启动脚本
./start.sh init

# 或手动初始化
python -c "
from src.database.connection import init_database
import asyncio

async def init():
    await init_database()
    print('数据库初始化完成')

asyncio.run(init())
"
```

## 5. 测试服务器功能

### 5.1 健康检查
```bash
curl http://localhost:8000/health
```

### 5.2 查看服务器信息
```bash
curl http://localhost:8000/
```

### 5.3 列出可用工具
```bash
curl http://localhost:8000/tools
```

### 5.4 执行测试（HTTP接口）
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "test_path": "tests/test_example.py",
    "project_name": "demo",
    "pytest_options": ["-v"]
  }'
```

### 5.5 MCP协议接口测试
```bash
# 初始化
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {"name": "test-client"},
      "capabilities": {}
    }
  }'

# 调用工具
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "run_pytest_tests",
      "arguments": {
        "test_path": "tests/test_example.py",
        "project_name": "demo"
      }
    }
  }'
```

## 6. 与 Goose 集成

### 6.1 配置 Goose
在 Goose 配置文件中添加：
```yaml
# ~/.goose/config.yaml 或项目中的 .goose/config.yaml
mcp_servers:
  pytest_test_server:
    command: "python"
    args: 
      - "-m"
      - "src.main"
      - "--host"
      - "0.0.0.0"
      - "--port"
      - "8000"
    env:
      MCP_PYTEST_DATABASE_URL: "sqlite:///./test_results.db"
```

### 6.2 环境变量配置
```bash
export GOOSE_MCP_SERVERS='{
  "pytest_test_server": {
    "command": "python",
    "args": ["-m", "src.main"],
    "env": {
      "MCP_PYTEST_DATABASE_URL": "sqlite:///./test_results.db"
    }
  }
}'
```

### 6.3 验证集成
启动 Goose 并测试：
```bash
# 启动 Goose
goose

# 在 Goose 会话中测试
# 用户：执行 pytest 测试
# Goose：我可以帮你执行 pytest 测试...
```

## 7. 生产环境部署

### 7.1 使用 systemd（Linux）
创建服务文件 `/etc/systemd/system/mcp-pytest.service`：
```ini
[Unit]
Description=MCP Pytest Test Server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/mcp-pytest-server
Environment="PATH=/opt/mcp-pytest-server/venv/bin"
Environment="MCP_PYTEST_DATABASE_URL=sqlite:///./test_results.db"
Environment="MCP_PYTEST_LOG_FILE=/var/log/mcp-pytest/server.log"
ExecStart=/opt/mcp-pytest-server/venv/bin/python -m src.main --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-pytest
sudo systemctl start mcp-pytest
sudo systemctl status mcp-pytest
```

### 7.2 使用 Docker
创建 `Dockerfile`：
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY src/ ./src/
COPY config/ ./config/
COPY tests/ ./tests/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "src.main", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：
```bash
# 构建镜像
docker build -t mcp-pytest-server .

# 运行容器
docker run -d \
  --name mcp-pytest \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  mcp-pytest-server
```

### 7.3 使用 Docker Compose
创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  mcp-pytest:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - MCP_PYTEST_DATABASE_URL=sqlite:///./data/test_results.db
      - MCP_PYTEST_LOG_FILE=/app/logs/server.log
      - MCP_PYTEST_DEBUG=false
    restart: unless-stopped
```

启动服务：
```bash
docker-compose up -d
docker-compose logs -f
```

## 8. 监控和维护

### 8.1 日志管理
```bash
# 查看日志
tail -f logs/server.log

# 日志轮转配置（logrotate）
# /etc/logrotate.d/mcp-pytest
/var/log/mcp-pytest/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 640 www-data www-data
    postrotate
        systemctl reload mcp-pytest > /dev/null 2>&1 || true
    endscript
}
```

### 8.2 性能监控
```bash
# 查看服务器状态
curl http://localhost:8000/health

# 查看数据库大小
ls -lh test_results.db

# 查看进程资源使用
ps aux | grep "src.main"
```

### 8.3 数据库维护
```bash
# 备份数据库
cp test_results.db test_results.db.backup.$(date +%Y%m%d)

# 清理旧数据（通过API）
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "cleanup_old_data",
      "arguments": {
        "days": 90
      }
    }
  }'
```

## 9. 故障排除

### 9.1 常见问题

**问题1**: 端口被占用
```bash
# 检查端口占用
sudo lsof -i :8000

# 停止占用进程
sudo kill -9 <PID>

# 或更改端口
python -m src.main --port 8080
```

**问题2**: 数据库连接失败
```bash
# 检查数据库文件权限
ls -la test_results.db

# 修复权限
chmod 644 test_results.db

# 重新初始化数据库
rm test_results.db
./start.sh init
```

**问题3**: 依赖安装失败
```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用conda
conda create -n mcp-pytest python=3.9
conda activate mcp-pytest
pip install -r requirements.txt
```

### 9.2 调试模式
```bash
# 启用调试模式
MCP_PYTEST_DEBUG=true python -m src.main

# 或使用参数
python -m src.main --debug

# 查看详细日志
tail -f logs/server.log
```

### 9.3 性能优化
```bash
# 调整数据库连接池
export MCP_PYTEST_DATABASE_POOL_SIZE=10
export MCP_PYTEST_DATABASE_MAX_OVERFLOW=20

# 调整pytest并行执行
export MCP_PYTEST_MAX_WORKERS=4

# 启用缓存
export MCP_PYTEST_CACHE_ENABLED=true
```

## 10. 安全考虑

### 10.1 网络安全
```bash
# 使用防火墙限制访问
sudo ufw allow 8000/tcp
sudo ufw enable

# 或使用反向代理（Nginx）
# nginx配置示例
location /mcp-pytest/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

### 10.2 认证和授权
```bash
# 启用API密钥认证
export MCP_PYTEST_API_KEY=your-secret-key

# 在请求中添加认证头
curl -H "X-API-Key: your-secret-key" http://localhost:8000/health
```

### 10.3 数据安全
```bash
# 加密数据库
export MCP_PYTEST_DATABASE_URL=sqlite:///./test_results.db?key=your-encryption-key

# 定期备份
0 2 * * * /usr/bin/cp /opt/mcp-pytest-server/test_results.db /backup/test_results.db.$(date +\%Y\%m\%d)
```

## 11. 扩展和定制

### 11.1 添加新工具
编辑 `src/mcp/handler.py`：
```python
def _register_default_tools(self):
    # ... 现有工具注册 ...
    
    self.register_tool(
        name="custom_tool",
        description="自定义工具",
        input_schema={
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "number"}
            }
        },
        handler=self._handle_custom_tool
    )

async def _handle_custom_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
    # 实现工具逻辑
    return {"result": "success"}
```

### 11.2 添加新资源
```python
def _register_default_resources(self):
    # ... 现有资源注册 ...
    
    self.register_resource(
        uri="custom://resource",
        name="自定义资源",
        description="自定义资源描述",
        mime_type="application/json"
    )
```

### 11.3 自定义数据库模型
编辑 `src/database/models.py`：
```python
class CustomModel(Base):
    __tablename__ = "custom_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 12. 支持与贡献

### 12.1 获取帮助
- 查看文档：`docs/` 目录
- 检查日志：`logs/server.log`
- 提交 Issue：项目 Issue 页面

### 12.2 报告问题
```bash
# 收集调试信息
python -m src.main --version
python --version
pip list
cat .env
```

### 12.3 贡献代码
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 创建 Pull Request

## 13. 更新和升级

### 13.1 更新依赖
```bash
# 更新所有依赖
pip install --upgrade -r requirements.txt

# 或更新特定包
pip install --upgrade fastapi pytest
```

### 13.2 数据库迁移
```bash
# 创建迁移脚本
alembic revision --autogenerate -m "添加新字段"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 13.3 版本升级
```bash
# 备份当前版本
cp -r mcp-pytest-server mcp-pytest-server-backup

# 获取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 重启服务
./start.sh stop
./start.sh start
```

---

通过本指南，您应该能够成功部署和配置 MCP Pytest 测试服务器。如有任何问题，请参考故障排除部分或提交 Issue。