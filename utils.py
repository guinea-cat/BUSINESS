"""
utils.py
功能工具集，提供 PDF 解析、网络搜索及数据预处理功能。
"""

import re
import json
import requests
from pypdf import PdfReader
from typing import List, Optional
import config

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    使用 pypdf 库从 PDF 文件中提取纯文本。

    参数:
        pdf_path (str): PDF 文件的存储路径。

    返回:
        str: 提取的文本。如果读取失败，返回包含错误说明的字符串。
    
    逻辑详解:
        1. 使用 PdfReader 加载文件。
        2. 遍历每一页，调用 extract_text() 方法。
        3. 拼接所有页面的文本并返回。
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
        return f"PDF 提取失败: {str(e)}"

def google_search(query: str) -> str:
    """
    通过 Serper.dev API 获取 Google 搜索结果。

    参数:
        query (str): 搜索关键词。

    返回:
        str: 前 5 条结果的标题和摘要拼接而成的字符串。
    
    逻辑详解:
        1. 构建 POST 请求到 Serper API 接口。
        2. 在 Header 中注入 config.SERPER_API_KEY。
        3. 解析 JSON 响应中的 'organic'（自然搜索结果）字段。
        4. 仅提取前 5 条，确保信息密度并防止上下文过长。
    """
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': config.SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = json.dumps({"q": query})

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status() # 如果状态码不是 200，抛出异常
        search_data = response.json()
        
        results = []
        # 'organic' 包含主要的网页结果
        for item in search_data.get('organic', [])[:5]:
            title = item.get('title', '无标题')
            snippet = item.get('snippet', '无内容')
            results.append(f"标题: {title}\n摘要: {snippet}\n")
            
        return "\n".join(results) if results else "未找到相关搜索结果。"
    except Exception as e:
        return f"搜索失败: {str(e)}"

def clean_json_string(text: str) -> str:
    """
    利用正则表达式从字符串中提取纯净的 JSON 内容。

    参数:
        text (str): 原始文本，可能包含 Markdown 标记或前导文字。

    返回:
        str: 提取出的 JSON 字符串。
    
    正则原理:
        1. 尝试匹配 ```json 和 ``` 之间的内容。
        2. 如果没找到，则寻找第一个 '{' 到最后一个 '}' 之间的内容。
    """
    # 步骤 1: 尝试寻找 Markdown 代码块形式的 JSON
    json_block_pattern = r"```json\s*(.*?)\s*```"
    match = re.search(json_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # 步骤 2: 备选方案，寻找第一个 { 和最后一个 }
    braces_pattern = r"(\{.*\})"
    match = re.search(braces_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # 如果都没找到，返回原文本（交由下游解析器报错或处理）
    return text.strip()
