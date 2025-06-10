from mcp.server import FastMCP
import os
import httpx
from dotenv import load_dotenv
import logging
import uuid
from typing import Dict, Any

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# 獲取環境變數
CHAT_API_URL = os.getenv("CHAT_API_URL")

# 創建 MCP 服務器
mcp = FastMCP("聊天服務")

@mcp.tool()
async def chat(message: str) -> Dict[str, Any]:
    """
    發送聊天訊息並獲取回應
    
    Args:
        message (str): 要發送的訊息
        
    Returns:
        Dict[str, Any]: 包含回應的字典
    """
    try:
        # 生成會話ID
        session_id = str(uuid.uuid4())
        
        # 準備請求數據
        request_data = {
            "sessionId": session_id,
            "chatInput": message
        }
        
        # 發送請求獲取聊天回應
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CHAT_API_URL,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            logger.info(f"API回應狀態碼: {response.status_code}")
            logger.info(f"API回應內容: {response.text}")
            
            response.raise_for_status()
            chat_data = response.json()
            
            return {
                "session_id": session_id,
                "message": message,
                "response": chat_data.get("output", "無回應")
            }
        
    except Exception as e:
        logger.error(f"處理請求時發生錯誤：{str(e)}")
        return {
            "error": str(e),
            "session_id": session_id if 'session_id' in locals() else None
        }

@mcp.tool()
def get_service_info() -> str:
    """獲取服務信息"""
    return """
【聊天服務信息】

此服務提供以下功能：
1. 發送聊天訊息並獲取回應
2. 自動生成唯一會話ID
3. 錯誤處理和日誌記錄

使用方法：
- 使用 chat 工具發送訊息並獲取回應
- 使用 get_service_info 獲取服務信息

環境配置：
- CHAT_API_URL: 聊天API的URL
"""

if __name__ == "__main__":
    mcp.run() 