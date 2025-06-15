from mcp.server import FastMCP
import os
import httpx
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List
import json

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# 獲取環境變數
N8N_API_URL = os.getenv("N8N_API_URL")
N8N_API_KEY = os.getenv("N8N_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # 用於生成工作流程

# 創建 MCP 服務器
mcp = FastMCP("n8n 工作流程設計助手")

@mcp.tool()
async def design_workflow(prompt: str) -> Dict[str, Any]:
    """
    根據提示詞設計n8n工作流程。
    
    Args:
        prompt (str): 工作流程需求描述。
        
    Returns:
        Dict[str, Any]: 如果成功，直接返回完整的n8n工作流程JSON物件。
                       如果失敗，返回包含 "status": "error" 和 "message" 的字典。
    """
    try:
        # 增加 GEMINI_API_KEY 檢查
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY 環境變數未設置")
            return {
                "status": "error",
                "message": "GEMINI_API_KEY 環境變數未設置，請確保已在 .env 檔案中配置。"
            }

        # 準備發送到 Gemini 的提示
        # Gemini 通常將系統提示詞整合到第一個用戶訊息中
        system_instructions_for_gemini = """
        你是一個n8n工作流程設計專家。請根據用戶的需求，設計一個完整的n8n工作流程。
        返回的格式必須是嚴格且有效的n8n工作流程JSON。
        必須包含以下頂層屬性：
        - "name" (字串): 工作流程的名稱。
        - "nodes" (陣列): 包含每個節點的物件。每個節點物件必須包含：
            - "name" (字串): 節點名稱。
            - "type" (字串): 節點類型 (例如 "n8n-nodes-base.webhook")。
            - "position" (陣列): 包含兩個數字的陣列，表示節點在畫布上的 [x, y] 座標。例如: [100, 200]。
            - "parameters" (物件): 節點的配置參數。
            - 其他必要的節點屬性。
        - "connections" (物件): 定義節點間的連接。
        - "active" (布林值): 工作流程是否啟用 (通常為true)。
        - "settings" (物件): 工作流程的設定 (至少包含 "executionOrder": "v1")。

        請確保你生成的JSON是完整的，可以直接被n8n的/workflows API接收。
        嚴禁包含 'id', 'versionId', 'meta', 'pinData', 'createdAt', 'updatedAt', 'tags' 這些自動生成或只在更新時使用的頂層屬性。
        """

        full_prompt_for_gemini = f"""
        {system_instructions_for_gemini}

        用戶需求描述: {prompt}
        請設計一個符合需求的工作流程，並返回完整的n8n工作流程JSON。
        """
        
        # 使用 Gemini 生成工作流程
        async with httpx.AsyncClient() as client:
            try:
                # Gemini API 端點和認證方式
                gemini_model = "gemini-2.0-flash" # 參考 test.json 中的模型，您也可以使用 "gemini-pro" 或其他版本
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent",
                    headers={
                        "x-goog-api-key": GEMINI_API_KEY, # Gemini 使用 x-goog-api-key
                        "Content-Type": "application/json"
                    },
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": full_prompt_for_gemini}]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.7
                        }
                    },
                    timeout=180 # 增加超時時間，給模型更多生成時間
                )
                
                response.raise_for_status() # 檢查HTTP錯誤 (例如 4xx, 5xx)

            except httpx.HTTPStatusError as e:
                # 捕獲 HTTP 狀態錯誤
                error_detail = ""
                try:
                    # 嘗試解析 Gemini 返回的錯誤 JSON
                    error_json = e.response.json()
                    error_detail = json.dumps(error_json, indent=2)
                except json.JSONDecodeError:
                    # 如果不是 JSON，則直接使用響應文本
                    error_detail = e.response.text
                
                logger.error(f"Gemini API 請求失敗 - HTTP 錯誤: {e.response.status_code}, 詳細: {error_detail}")
                return {
                    "status": "error",
                    "message": f"呼叫Gemini API失敗 (HTTP {e.response.status_code})。詳細訊息: {error_detail}"
                }
            except httpx.RequestError as e:
                # 捕獲網路相關錯誤
                logger.error(f"Gemini API 請求失敗 - 網路錯誤: {str(e)}")
                return {
                    "status": "error",
                    "message": f"呼叫Gemini API失敗 (網路錯誤): {str(e)}"
                }
            except Exception as e:
                # 捕獲 httpx 請求過程中其他未預期的錯誤
                logger.error(f"Gemini API 請求時發生未知錯誤: {str(e)}")
                return {
                    "status": "error",
                    "message": f"呼叫Gemini API時發生未知錯誤: {str(e)}"
                }
            
            # --- 繼續處理成功的響應 ---
            try:
                gemini_response_data = response.json()
                # 檢查 Gemini 響應結構
                if not gemini_response_data or "candidates" not in gemini_response_data or not gemini_response_data["candidates"]:
                    logger.error(f"Gemini API 返回非預期結構或空響應: {response.text}")
                    return {
                        "status": "error",
                        "message": f"Gemini API 返回非預期結構或空響應。原始響應: {response.text[:200]}..."
                    }
                
                # 從 Gemini 響應中提取生成的內容
                workflow_json_content = gemini_response_data["candidates"][0]["content"]["parts"][0]["text"]

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"解析Gemini響應或提取內容失敗: {str(e)}, 原始響應: {response.text}")
                return {
                    "status": "error",
                    "message": f"解析Gemini響應失敗: {str(e)}。原始響應: {response.text[:200]}..."
                }
            
            # 模型有時會在JSON前後添加額外文字，嘗試提取JSON
            if workflow_json_content.startswith("```json"):
                workflow_json_content = workflow_json_content.strip("```json\n").strip("```")
            
            # 驗證並格式化工作流程JSON
            try:
                workflow_data = json.loads(workflow_json_content)

                # 再次檢查和修正基本結構 (保險措施)
                if "nodes" not in workflow_data:
                    workflow_data["nodes"] = []
                if "connections" not in workflow_data:
                    workflow_data["connections"] = {}
                if "name" not in workflow_data:
                    workflow_data["name"] = "Generated Workflow" # 提供預設名稱
                if "active" not in workflow_data:
                    workflow_data["active"] = False # 預設為非啟用
                if "settings" not in workflow_data:
                    workflow_data["settings"] = {"executionOrder": "v1"} # 提供預設設定
                
                # --- 核心修改：直接返回 workflow_data ---
                return workflow_data 
                # --- 核心修改結束 ---

            except json.JSONDecodeError:
                logger.error(f"生成的工作流程JSON格式無效: {workflow_json_content}")
                return {
                    "status": "error",
                    "message": f"生成的工作流程格式無效，無法解析為JSON。原始響應: {workflow_json_content[:200]}..." # 顯示部分響應
                }
                
    except Exception as e: # 捕獲外層 try 區塊中任何其他未預期的錯誤
        logger.error(f"設計工作流程時發生未知錯誤 (外層捕捉): {str(e)}")
        return {
            "status": "error",
            "message": f"設計工作流程時發生未知錯誤: {str(e)}"
        }

@mcp.tool()
async def create_workflow(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    在n8n中創建新的工作流程
    
    Args:
        workflow_data (Dict[str, Any]): 工作流程數據
        
    Returns:
        Dict[str, Any]: 創建結果
    """
    try:
        logger.info(f"create_workflow 接收到的原始數據: {json.dumps(workflow_data, indent=2)}")

        if not N8N_API_URL or not N8N_API_KEY:
            logger.error("N8N_API_URL 或 N8N_API_KEY 環境變數未設置")
            return {
                "status": "error",
                "message": "N8N_API_URL 或 N8N_API_KEY 環境變數未設置，請確保已在 .env 檔案中配置。"
            }

        if not isinstance(workflow_data, dict):
            return {
                "status": "error",
                "message": "傳入的工作流程數據必須是字典格式"
            }
        # 移除對 nodes/connections/name 的驗證，因為我們會在後面修正它們
        # if "nodes" not in workflow_data or "connections" not in workflow_data or "name" not in workflow_data:
        #     return {
        #         "status": "error",
        #         "message": "傳入的工作流程數據不符合n8n工作流程JSON的預期結構，缺少 'nodes', 'connections' 或 'name' 關鍵字。"
        #     }

        # --- 核心修改：更新需要移除的頂層屬性列表 ---
        cleaned_workflow_data = workflow_data.copy()
        
        # 將 'tags' 和 'active' 也加入需要移除的鍵列表中，以及其他自動生成的屬性
        keys_to_remove = ["id", "versionId", "meta", "pinData", "createdAt", "updatedAt", "active", "tags"] 
        
        for key in keys_to_remove:
            if key in cleaned_workflow_data:
                del cleaned_workflow_data[key]
        
        # --- 新增：處理 nodes 內部結構，特別是 'position' ---
        if "nodes" in cleaned_workflow_data and isinstance(cleaned_workflow_data["nodes"], list):
            for i, node in enumerate(cleaned_workflow_data["nodes"]):
                if "position" in node:
                    pos = node["position"]
                    if not isinstance(pos, list):
                        logger.warning(f"Node {i} 的 'position' 非陣列格式 ({type(pos)}: {pos})，嘗試修正。")
                        if isinstance(pos, str):
                            try:
                                # 嘗試從字符串解析，例如 "100, 200"
                                coords = [int(x.strip()) for x in pos.split(',')]
                                if len(coords) == 2:
                                    node["position"] = coords
                                else:
                                    logger.warning(f"Node {i} 的 'position' 字符串無法解析為兩個數字：{pos}")
                                    node["position"] = [0, 0] # 設置為預設值
                            except ValueError:
                                logger.warning(f"Node {i} 的 'position' 字符串無法轉換為數字：{pos}")
                                node["position"] = [0, 0] # 設置為預設值
                        elif isinstance(pos, (int, float)):
                            # 如果是單一數字，可以假設是 X 座標，Y 設為 0
                            node["position"] = [int(pos), 0]
                        else:
                            # 對於其他不可預期的類型，設置為預設值
                            logger.warning(f"Node {i} 的 'position' 類型不可預期 ({type(pos)})，設置為預設值。")
                            node["position"] = [0, 0]
                else:
                    # 如果缺少 position 屬性，給予預設值
                    node["position"] = [0, 0]
        # --- 新增結束 ---

        logger.info(f"create_workflow 發送給 n8n API 的數據 (已清理): {json.dumps(cleaned_workflow_data, indent=2)}")
        # --- 核心修改結束 ---

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{N8N_API_URL}/workflows",
                    headers={"X-N8N-API-KEY": N8N_API_KEY},
                    json=cleaned_workflow_data,
                    timeout=30
                )
                
                response.raise_for_status()

            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_json = e.response.json()
                    error_detail = json.dumps(error_json, indent=2)
                except json.JSONDecodeError:
                    error_detail = e.response.text
                
                logger.error(f"n8n API 創建工作流程失敗 - HTTP 錯誤: {e.response.status_code}, 詳細: {error_detail}")
                return {
                    "status": "error",
                    "message": f"呼叫n8n API創建工作流程失敗 (HTTP {e.response.status_code})。詳細訊息: {error_detail}"
                }
            except httpx.RequestError as e:
                logger.error(f"n8n API 創建工作流程失敗 - 網路錯誤: {str(e)}")
                return {
                    "status": "error",
                    "message": f"呼叫n8n API創建工作流程失敗 (網路錯誤): {str(e)}"
                }
            except Exception as e:
                logger.error(f"n8n API 請求時發生未知錯誤: {str(e)}")
                return {
                    "status": "error",
                    "message": f"呼叫n8n API創建工作流程時發生未知錯誤: {str(e)}"
                }
            
            return {
                "status": "success",
                "data": response.json(),
                "message": "工作流程已成功創建"
            }
                
    except Exception as e:
        logger.error(f"創建工作流程時發生未知錯誤 (外層捕捉): {str(e)}")
        return {
            "status": "error",
            "message": f"創建工作流程時發生未知錯誤: {str(e)}"
        }

@mcp.tool()
def get_service_info() -> str:
    """獲取服務信息"""
    return """
【n8n 工作流程設計助手】

此服務提供以下功能：
1. 根據提示詞設計n8n工作流程 (直接返回 n8n 工作流程 JSON)
2. 自動創建設計好的工作流程

使用方法：
- 使用 design_workflow 設計工作流程：
  * 提供需求描述
  * **返回：** 直接是 n8n 工作流程的 JSON 物件 (Dict[str, Any])
- 使用 create_workflow 創建工作流程：
  * **輸入：** 需傳入 design_workflow 返回的完整 n8n 工作流程 JSON 物件作為 'workflow_data' 參數。
- 使用 get_service_info 獲取服務信息

環境配置：
- N8N_API_URL: n8n API的URL
- N8N_API_KEY: n8n API金鑰
- GEMINI_API_KEY: Google Gemini API金鑰 (取代 OPENAI_API_KEY)
"""

if __name__ == "__main__":
    mcp.run() 