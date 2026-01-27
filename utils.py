"""
utils.py
功能工具集，提供 PDF 解析、网络搜索及数据清洗功能。
所有网络请求均包含完整的异常处理逻辑。
"""

import re
import json
import logging
import requests
import fitz  # PyMuPDF
import io
import base64
from PIL import Image
from typing import List, Optional, Dict
import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_content_from_pdf(pdf_path: str) -> Dict[str, any]:
    """
    使用 PyMuPDF 从 PDF 中提取文本和图像内容。
    优化：对提取的图像进行缩放和压缩，减少上传带宽消耗。
    """
    full_text = ""
    images_base64 = []
    
    try:
        doc = fitz.open(pdf_path)
        for page_index in range(len(doc)):
            page = doc[page_index]
            
            # 1. 提取文本
            full_text += page.get_text() + "\n"
            
            # 2. 提取图像
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # 过滤太小的图标类图片 (例如小于 5KB)
                if len(image_bytes) < 5000:
                    continue
                
                # --- 优化：图片缩放与压缩，减小上传体积 ---
                try:
                    img_obj = Image.open(io.BytesIO(image_bytes))
                    # 如果宽度超过 1024，进行等比例缩放
                    if img_obj.width > 1024:
                        ratio = 1024 / img_obj.width
                        new_size = (1024, int(img_obj.height * ratio))
                        img_obj = img_obj.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # 转换为 JPEG 并压缩画质为 75
                    if img_obj.mode in ("RGBA", "P"):
                        img_obj = img_obj.convert("RGB")
                    
                    buffer = io.BytesIO()
                    img_obj.save(buffer, format="JPEG", quality=75)
                    image_bytes = buffer.getvalue()
                    img_ext = "jpg"
                except Exception as e:
                    logger.warning(f"图片处理失败，保留原图: {e}")
                    img_ext = base_image["ext"]

                # 转换为 base64 以便后续传给 VLM
                base64_img = base64.b64encode(image_bytes).decode('utf-8')
                images_base64.append({
                    "page": page_index + 1,
                    "data": base64_img,
                    "ext": img_ext
                })
        
        doc.close()
        return {
            "text": full_text.strip(),
            "images": images_base64[:50]  # 限制提取前 50 张重要图片，平衡深度与速度
        }
    except Exception as e:
        logger.error(f"解析 PDF 失败: {pdf_path}, 错误: {e}")
        return {"text": f"PDF 提取失败: {str(e)}", "images": []}

def describe_visual_elements(client, images: List[Dict]) -> str:
    """
    调用多模态模型对提取的图片进行理解和描述。
    """
    if not images:
        return "未发现显著视觉元素。"
        
    visual_context = "### 🖼️ 商业计划书视觉元素分析\n"
    
    for i, img in enumerate(images):
        prompt = "这是一张商业计划书（BP）中的图片，请分析其中的关键信息（如数据图表趋势、商业模式图解、产品原型特征或财务预测数据）。请简洁明了地描述图片内容。"
        
        try:
            # 注意：此处假设使用的是支持多模态的 OpenAI 兼容接口
            response = client.chat.completions.create(
                model=config.VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/{img['ext']};base64,{img['data']}"}
                            }
                        ],
                    }
                ],
                max_tokens=500
            )
            description = response.choices[0].message.content
            visual_context += f"**[图表 {i+1} (第 {img['page']} 页)]**: {description}\n\n"
        except Exception as e:
            logger.warning(f"分析图片 {i+1} 失败: {e}")
            continue
            
    return visual_context

def google_search(query: str, start_id: int = 1) -> str:
    """
    使用 Serper.dev API 获取 Google 搜索结果。
    """
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': config.SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = json.dumps({"q": query})

    try:
        logger.info(f"正在发起搜索请求: {query}")
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        search_data = response.json()
        
        results = []
        for i, item in enumerate(search_data.get('organic', [])[:5], start_id):
            title = item.get('title', '无标题')
            snippet = item.get('snippet', '无内容')
            url_link = item.get('link', '无链接')
            results.append(f"[S{i}] URL: {url_link} Title: {title} Snippet: {snippet}")
            
        if not results:
            logger.warning(f"关键词 '{query}' 未找到相关搜索结果。")
            return ""
            
        return "\n".join(results)
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求失败: {e}")
        return f"网络搜索异常: {str(e)}"
    except Exception as e:
        logger.error(f"解析搜索结果失败: {e}")
        return f"搜索结果处理异常: {str(e)}"

def clean_json_string(text: str) -> str:
    """
    从 LLM 输出的原始文本中提取 JSON 字符串。
    """
    json_block_pattern = r"```json\s*(.*?)\s*```"
    match = re.search(json_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    braces_pattern = r"(\{.*\})"
    match = re.search(braces_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return text.strip()

def extract_funding_amounts(text: str) -> List[str]:
    """
    利用正则表达式从文本中提取融资金额。
    """
    patterns = [
        r"\d+\.?\d*\s*亿\s*(美元|元|RMB|USD)?",
        r"\d+\.?\d*\s*万\s*(美元|元|RMB|USD)?",
        r"\d+\.?\d*\s*(million|billion)\s*(USD|RMB)?",
        r"[A-Z]轮\d+\.?\d*亿"
    ]
    
    results = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                full_matches = [m.group(0) for m in re.finditer(pattern, text, re.IGNORECASE)]
                results.extend(full_matches)
            else:
                results.extend(matches)
    
    return list(set(results))[:5]
