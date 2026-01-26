"""
utils.py
功能工具集，提供 PDF 解析、网络搜索及数据清洗功能。
所有网络请求均包含完整的异常处理逻辑。
"""

import re
import json
import logging
import requests
from pypdf import PdfReader
from typing import List, Optional
import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    从 PDF 文件中提取纯文本内容。

    参数:
        pdf_path (str): PDF 文件路径。

    返回:
        str: 提取的纯文本内容。若失败则返回错误提示。
    """
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"解析 PDF 失败: {pdf_path}, 错误: {e}")
        return f"PDF 提取失败: {str(e)}"

def google_search(query: str) -> str:
    """
    使用 Serper.dev API 获取 Google 搜索结果。
    包含完整的网络异常捕获和状态码检查。

    参数:
        query (str): 搜索关键词。

    返回:
        str: 格式化后的搜索摘要结果。
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
        for item in search_data.get('organic', [])[:5]:
            title = item.get('title', '无标题')
            snippet = item.get('snippet', '无内容')
            results.append(f"标题: {title}\n摘要: {snippet}\n")
            
        if not results:
            logger.warning(f"关键词 '{query}' 未找到相关搜索结果。")
            return "未找到相关搜索结果。"
            
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
    支持 Markdown 代码块及原始花括号提取。

    参数:
        text (str): LLM 输出内容。

    返回:
        str: 清洗后的 JSON 字符串。
    """
    # 匹配 Markdown 代码块
    json_block_pattern = r"```json\s*(.*?)\s*```"
    match = re.search(json_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # 匹配第一个和最后一个大括号
    braces_pattern = r"(\{.*\})"
    match = re.search(braces_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return text.strip()

def extract_funding_amounts(text: str) -> List[str]:
    """
    利用正则表达式从文本中提取融资金额。

    参数:
        text (str): 待处理文本。

    返回:
        List[str]: 提取到的金额列表。
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
        # re.findall 返回 tuple 如果有分组，这里简化处理
        if matches:
            if isinstance(matches[0], tuple):
                # 重新搜索以获取完整匹配项
                full_matches = [m.group(0) for m in re.finditer(pattern, text, re.IGNORECASE)]
                results.extend(full_matches)
            else:
                results.extend(matches)
    
    return list(set(results))[:5]
