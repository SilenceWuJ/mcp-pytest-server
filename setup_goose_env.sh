#!/bin/bash
# Goose MCP环境设置脚本

export GOOSE_MCP_SERVERS='{
  "pytest_test_server": {
    "command": "/Users/xixi/mcp-pytest-server/venv/bin/python3",
    "args": ["simple_server.py"],
    "env": {
      "PYTHONPATH": "/Users/xixi/mcp-pytest-server"
    }
  }
}'

echo "Goose MCP环境已设置"
echo "现在可以启动Goose: goose"
