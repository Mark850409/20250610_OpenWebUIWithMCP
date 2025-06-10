# ⚡️ mcpo+OpenWebUI 結合MCP的開源聊天工具

## 📁 專案架構

### 核心功能
- MCP 工具轉換為 OpenAPI 兼容的 HTTP 服務器
- 支援多種 MCP 服務器類型
- 自動生成 API 文檔
- 提供安全認證機制

### 支援的服務器類型
1. 標準 MCP 服務器
2. SSE 兼容服務器
3. Streamable HTTP 兼容服務器

## 🚀 部署方式

### 系統需求
- Python 3.8+
- uv（推薦）

### 部署選項

1. **使用 uv 部署**
```bash
uvx mcpo --port 8000 --api-key "top-secret" -- your_mcp_server_command
```

2. **使用 Python pip 部署**
```bash
pip install mcpo
mcpo --port 8000 --api-key "top-secret" -- your_mcp_server_command
```

3. **使用 Docker 部署**
```bash
docker run -p 8000:8000 ghcr.io/open-webui/mcpo:main --api-key "top-secret" -- your_mcp_server_command
```

## 🐳 Docker 部署

### 使用 Docker 啟動

1. **直接使用 Docker 映像**
```bash
docker run -p 8000:8000 ghcr.io/open-webui/mcpo:main --api-key "top-secret" -- your_mcp_server_command
```

2. **使用 docker-compose 啟動**
```bash
# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### Docker 部署注意事項

1. **環境配置**
- 使用 `.env` 文件管理 API 密鑰等敏感信息
- 可通過環境變數覆蓋預設配置

2. **訪問路徑**
- 主服務器：http://localhost:8000
- API 文檔：http://localhost:8000/docs

3. **安全建議**
- 生產環境請修改預設端口
- 使用強密碼作為 API 密鑰
- 定期更新 Docker 映像



## 📝 語法說明

### 基本命令格式
```bash
mcpo [選項] -- 命令
```

### 常用選項
- `--port`: 指定服務器端口（預設：8000）
- `--api-key`: 設置 API 密鑰
- `--server-type`: 指定服務器類型（sse/streamable_http）
- `--config`: 指定配置文件路徑

### 配置文件格式
```json
{
  "mcpServers": {
    "服務器名稱": {
      "command": "命令",
      "args": ["參數1", "參數2"],
      "type": "服務器類型",  // 可選
      "url": "服務器URL"     // 可選
    }
  }
}
```

### 服務器類型配置

1. **標準 MCP 服務器**
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"]
}
```

2. **SSE 服務器**
```json
{
  "type": "sse",
  "url": "http://127.0.0.1:8001/sse"
}
```

3. **Streamable HTTP 服務器**
```json
{
  "type": "streamable_http",
  "url": "http://127.0.0.1:8002/mcp"
}
```

## 🔧 開發環境設置

1. **克隆專案**
```bash
git clone https://github.com/open-webui/mcpo.git
cd mcpo
```

2. **安裝依賴**
```bash
uv sync --dev
```

3. **運行測試**
```bash
uv run pytest
```

## ⚠️ 注意事項

### 安全建議
- 始終使用 API key 保護服務器
- 避免在生產環境使用預設端口
- 定期更新依賴包

### 訪問路徑
- 主服務器：http://localhost:8000
- API 文檔：http://localhost:8000/docs
- 工具特定文檔：http://localhost:8000/<tool>/docs

### 常見問題
1. 確保 Python 版本符合要求
2. 檢查端口是否被占用
3. 驗證 API key 設置
4. 確認服務器類型配置正確

## 📚 相關資源
- [GitHub 倉庫](https://github.com/open-webui/mcpo)
- [OpenAPI 文檔](http://localhost:8000/docs)
- [MCP 協議文檔](https://modelcontextprotocol.io)

## 🤝 貢獻指南
歡迎提交 Pull Request 或開 Issue 討論新功能。