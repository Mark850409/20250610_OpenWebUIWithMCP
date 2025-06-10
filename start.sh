#!/bin/bash
set -e # 有任何指令失敗就退出

# 確保 config 目錄存在
mkdir -p /app/config

# 啟動 mcpo (使用配置文件並在後台執行)
echo "正在啟動 mcpo..."
if [ -f "/app/config/config.json" ]; then
  mcpo --config /app/config/config.json --port 8000 &
  MCPO_PID=$! # 記錄 mcpo 的 process ID
  echo "mcpo 已啟動 (PID: $MCPO_PID)"
else
  echo "警告: 未找到 /app/config/config.json，mcpo 將不會啟動。"
  echo "請掛載 config.json 到 /app/config/config.json 以啟用 mcpo。"
  # 如果 mcpo 未啟動，設置一個假的 PID 或退出，取決於 mcpo 是否是強制依賴
  # 這裡假設 open-webui 可以獨立啟動但無法使用 mcpo 功能
  MCPO_PID=0 
fi

# 啟動 open-webui
echo "正在啟動 open-webui..."
# Open WebUI 通常會監聽 8080，確保 mcpo 服務位址正確
# 如果 mcpo 運行在容器內，open-webui 需連到 localhost:8000
# 這裡透過環境變數設定給 open-webui
OPENWEBUI_OLLAMA_BASE_URL="http://localhost:8000" \
OPENWEBUI_HOST="0.0.0.0" \
open-webui serve --host 0.0.0.0 --port 8080

# 等待 mcpo 結束 (如果啟動了)
if [ "$MCPO_PID" -ne 0 ]; then
  wait $MCPO_PID
fi

echo "服務已停止"