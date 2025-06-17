import os
import logging
from dotenv import load_dotenv
from mcp.server import FastMCP
import httpx
import json

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# 創建 MCP 服務
mcp = FastMCP("Flux 圖片生成服務")

@mcp.tool()
async def generate_flux_image(
    prompt: str,
    count: int = 1,
    format: str = "png",
    quality: int = 100,
    aspect_ratio: str = "1:1",
    model: str = "flux-dev"
) -> str:
    """
    生成圖片的工具

    Args:
        prompt (str): 圖片生成的提示詞
        count (int): 生成數量，預設 1
        format (str): 圖片格式，預設 png
        quality (int): 圖片品質，預設 100
        aspect_ratio (str): 長寬比，預設 1:1
        model (str): 模型名稱，預設 flux-dev

    Returns:
        str: Markdown 格式的圖片連結
    """
    logger.info(f"開始生成圖片，提示詞：{prompt}")
    logger.info(f"參數設置 - 數量：{count}, 格式：{format}, 品質：{quality}, 比例：{aspect_ratio}, 模型：{model}")

    url = os.getenv("FLUX_IMAGE_WEBHOOK_URL")
    if not url:
        return "錯誤：未設置 FLUX_IMAGE_WEBHOOK_URL"

    # 型別保證
    if aspect_ratio is not None and not isinstance(aspect_ratio, str):
        aspect_ratio = str(aspect_ratio)
    if format is not None and not isinstance(format, str):
        format = str(format)
    if quality is not None and not isinstance(quality, int):
        try:
            quality = int(quality)
        except Exception:
            return "錯誤：quality 參數無法轉為 int"
    if model is not None and not isinstance(model, str):
        model = str(model)

    # 組裝 payload
    payload = {
        "prompt": prompt,
        "count": count,
        "format": format,
        "quality": quality,
        "aspect_ratio": aspect_ratio,
        "model": model,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    logger.info(f"Webhook payload: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60)
            if response.status_code != 200:
                return f"API 請求錯誤：狀態碼 {response.status_code}"

            data = response.json()
            image_links = data.get("image_urls") or data.get("圖片連結", "[]")
            # image_links 可能是字串型態的 JSON 陣列
            if isinstance(image_links, str):
                try:
                    image_objs = json.loads(image_links)
                except Exception:
                    image_objs = []
            else:
                image_objs = image_links

            # image_objs 可能是 [{'url': ...}] 或直接是 url 字串陣列
            image_urls = []
            if isinstance(image_objs, list):
                for item in image_objs:
                    if isinstance(item, dict) and "url" in item:
                        image_urls.append(item["url"])
                    elif isinstance(item, str):
                        image_urls.append(item)

            if not image_urls:
                return "錯誤：API 返回空回應"

            image_url = image_urls[0]
            if not image_url.startswith(('http://', 'https://')):
                logger.error(f'無效的圖片 URL: {image_url}')
                return "錯誤：收到無效的圖片 URL"

            logger.info(f"成功獲取圖片 URL：{image_url}")

            # 返回 Markdown 格式的圖片
            return f"""
### 生成的圖片

![Generated Image]({image_url})

[點擊查看原圖]({image_url})
"""
    except httpx.TimeoutException as e:
        logger.error(f'請求超時: {e}')
        return "錯誤：請求超時，請稍後再試"
    except httpx.RequestError as e:
        logger.error(f'API 請求錯誤: {e}')
        return f"API 請求錯誤：{str(e)}"
    except Exception as e:
        logger.error(f'發生未知錯誤: {e}')
        return f"發生錯誤：{str(e)}"

@mcp.tool()
def get_flux_service_info() -> str:
    """獲取 Flux 圖片生成服務的基本信息"""
    return """
【Flux 圖片生成服務】

此服務提供以下功能：
1. 基於文字提示生成圖片
2. 支持自定義生成數量、格式、品質、長寬比、模型名稱

參數說明：
- prompt: 圖片生成的提示詞（必填）
- count: 生成數量（可選，預設 1）
- format: 圖片格式（可選，預設 png）
- quality: 圖片品質（可選，預設 100）
- aspect_ratio: 長寬比（可選，預設 1:1）
- model: 模型名稱（可選，預設 flux-dev）

使用 generate_flux_image 工具生成圖片
使用 get_flux_service_info 工具獲取服務信息
"""

if __name__ == "__main__":
    mcp.run() 