"""
utils.py
功能工具集，提供 PDF 解析、网络搜索及数据清洗功能。
优化版：引入并发机制和图片拼接策略，大幅提升分析速度。
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_content_from_pdf(pdf_path: str) -> Dict[str, any]:
    """
    使用 PyMuPDF 从 PDF 中提取文本和图像内容。
    优化策略：
    1. 过滤异常长宽比图片（页眉页脚线条）
    2. 按文件体积排序，优先分析复杂图表
    3. 限制最大分析数量为 50 张
    """
    full_text = ""
    images_with_size = []  # 存储 (图片数据, 文件体积) 元组
    
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
                
                # --- 新增：过滤异常长宽比的图片 ---
                try:
                    img_obj = Image.open(io.BytesIO(image_bytes))
                    aspect_ratio = img_obj.width / img_obj.height if img_obj.height > 0 else 0
                    
                    # 过滤长宽比 > 5:1 或 < 1:5 的图片（通常是页眉页脚线条）
                    if aspect_ratio > 5 or aspect_ratio < 0.2:
                        logger.debug(f"跳过异常长宽比图片: {aspect_ratio:.2f}")
                        continue
                    
                    # 缩放与压缩
                    if img_obj.width > 1024:
                        ratio = 1024 / img_obj.width
                        new_size = (1024, int(img_obj.height * ratio))
                        img_obj = img_obj.resize(new_size, Image.Resampling.LANCZOS)
                    
                    if img_obj.mode in ("RGBA", "P"):
                        img_obj = img_obj.convert("RGB")
                    
                    buffer = io.BytesIO()
                    img_obj.save(buffer, format="JPEG", quality=75)
                    image_bytes = buffer.getvalue()
                    img_ext = "jpg"
                except Exception as e:
                    logger.warning(f"图片处理失败，保留原图: {e}")
                    img_ext = base_image["ext"]

                # 存储图片及其体积（用于后续排序）
                base64_img = base64.b64encode(image_bytes).decode('utf-8')
                images_with_size.append({
                    "page": page_index + 1,
                    "data": base64_img,
                    "ext": img_ext,
                    "size": len(image_bytes)
                })
        
        doc.close()
        
        # --- 按体积排序，选取最大的 50 张（分析所有有效图片）---
        images_with_size.sort(key=lambda x: x["size"], reverse=True)
        selected_images = [
            {"page": img["page"], "data": img["data"], "ext": img["ext"]}
            for img in images_with_size[:50]  # 最多分析 50 张
        ]
        
        logger.info(f"PDF 解析完成：提取 {len(images_with_size)} 张有效图片，将分析 {len(selected_images)} 张")
        
        return {
            "text": full_text.strip(),
            "images": selected_images
        }
    except Exception as e:
        logger.error(f"解析 PDF 失败: {pdf_path}, 错误: {e}")
        return {"text": f"PDF 提取失败: {str(e)}", "images": []}


def stitch_images(images: List[Dict], grid_size: int = 3) -> List[Dict]:
    """
    将图片按网格拼接,减少 API 请求次数。
    
    参数:
        images: 原始图片列表
        grid_size: 网格大小（默认 3x3，即 9 张拼成 1 张）
    
    返回:
        拼接后的图片列表
    """
    stitched_images = []
    batch_size = grid_size * grid_size
    
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        
        if len(batch) == 1:
            # 只有 1 张，直接保留
            stitched_images.append(batch[0])
            continue
        
        try:
            # 解码 base64 图片
            pil_images = []
            for img in batch:
                img_data = base64.b64decode(img["data"])
                pil_images.append(Image.open(io.BytesIO(img_data)))
            
            # 计算拼接后的画布大小
            max_width = max(img.width for img in pil_images)
            max_height = max(img.height for img in pil_images)
            
            # 创建空白画布
            canvas_width = max_width * grid_size
            canvas_height = max_height * grid_size
            canvas = Image.new('RGB', (canvas_width, canvas_height), (255, 255, 255))
            
            # 粘贴图片到网格
            for idx, pil_img in enumerate(pil_images):
                row = idx // grid_size
                col = idx % grid_size
                x = col * max_width + (max_width - pil_img.width) // 2
                y = row * max_height + (max_height - pil_img.height) // 2
                canvas.paste(pil_img, (x, y))
            
            # 转换回 base64
            buffer = io.BytesIO()
            canvas.save(buffer, format="JPEG", quality=80)
            stitched_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            stitched_images.append({
                "data": stitched_data,
                "ext": "jpg",
                "pages": [img["page"] for img in batch],
                "count": len(batch)
            })
            
        except Exception as e:
            logger.warning(f"拼接图片失败，保留原图: {e}")
            stitched_images.extend(batch)
    
    logger.info(f"图片拼接完成：{len(images)} 张 → {len(stitched_images)} 张（减少 {len(images) - len(stitched_images)} 次请求）")
    return stitched_images


def _analyze_single_image(client, img: Dict, index: int) -> tuple:
    """
    分析单张图片的工作函数（用于并发执行）。
    支持拼接图和普通图两种模式。
    
    返回: (index, page_info, description) 元组
    """
    try:
        # 判断是否为拼接图（由 stitch_images 函数添加 count 字段）
        if "count" in img:
            prompt = f"这是 {img['count']} 张商业计划书图片的拼贴（按 3x3 网格排列）。请从左到右、从上到下逐个描述每张图的核心内容（如数据图表、商业模式图、产品原型或财务预测）。"
            page_info = f"拼贴图 (第 {', '.join(map(str, img['pages']))} 页)"
        else:
            prompt = "这是一张商业计划书（BP）中的图片，请分析其中的关键信息（如数据图表趋势、商业模式图解、产品原型特征或财务预测数据）。请简洁明了地描述图片内容。"
            page_info = f"第 {img['page']} 页"
        
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
        logger.info(f"图片 {index + 1} 分析完成")
        return (index, page_info, description)
        
    except Exception as e:
        logger.warning(f"分析图片 {index + 1} 失败: {e}")
        return (index, None, None)


def describe_visual_elements(client, images: List[Dict]) -> str:
    """
    并发调用多模态模型对提取的图片进行理解和描述。
    优化策略：
    1. 使用 3x3 拼图策略，将 9 张图拼成 1 张（减少 89% API 请求）
    2. 使用 ThreadPoolExecutor 并发执行（max_workers=10）
    """
    if not images:
        return "未发现显著视觉元素。"
    
    logger.info(f"检测到 {len(images)} 张有效图片，正在进行 3x3 拼图...")
    
    # 1. 拼接图片（9 张拼成 1 张）
    stitched_images = stitch_images(images, grid_size=3)
    logger.info(f"图片拼接完成：{len(images)} 张 → {len(stitched_images)} 张（减少 {len(images) - len(stitched_images)} 次请求）")
    
    # 2. 并发分析拼接后的图片
    visual_context = "### 🖼️ 商业计划书视觉元素分析\n"
    results = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_analyze_single_image, client, img, i): i 
            for i, img in enumerate(stitched_images)  # 分析拼接后的图片
        }
        
        for future in as_completed(futures):
            index, page_info, description = future.result()
            if description:
                results[index] = (page_info, description)
    
    # 3. 按原始顺序组装结果
    for i in sorted(results.keys()):
        page_info, description = results[i]
        visual_context += f"**[图表 {i+1} ({page_info})]**: {description}\n\n"
    
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


def repair_json(json_str: str) -> str:
    """
    尝试修复截断或格式错误的 JSON 字符串。
    
    修复策略：
    1. 尝试直接解析
    2. 如果失败，尝试补全缺失的右大括号 } 或右中括号 ]
    3. 如果仍然失败，返回空字典 {} 并记录错误日志
    
    参数:
        json_str: 待修复的 JSON 字符串
    
    返回:
        修复后的 JSON 字符串（如果无法修复则返回 "{}")
    """
    # 第一次尝试：直接解析
    try:
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 解析失败，尝试自动修复: {e}")
    
    # 第二次尝试：补全缺失的括号
    repaired = json_str.rstrip()
    
    # 统计括号数量
    open_braces = repaired.count('{')
    close_braces = repaired.count('}')
    open_brackets = repaired.count('[')
    close_brackets = repaired.count(']')
    
    # 补全缺失的右中括号
    if open_brackets > close_brackets:
        repaired += ']' * (open_brackets - close_brackets)
        logger.info(f"补全了 {open_brackets - close_brackets} 个右中括号 ]")
    
    # 补全缺失的右大括号
    if open_braces > close_braces:
        repaired += '}' * (open_braces - close_braces)
        logger.info(f"补全了 {open_braces - close_braces} 个右大括号 }}")
    
    # 再次尝试解析
    try:
        json.loads(repaired)
        logger.info("JSON 修复成功")
        return repaired
    except json.JSONDecodeError as e:
        logger.error(f"JSON 修复失败，返回空字典: {e}")
        logger.error(f"原始 JSON 片段: {json_str[:200]}...")
        return "{}"


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
