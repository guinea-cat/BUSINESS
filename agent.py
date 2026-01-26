"""
agent.py
商业分析智能体核心模块，负责协调 PDF 解析、搜索调度和 LLM 分析。
"""

import json
import traceback
from typing import List, Dict
from openai import OpenAI
import config
import utils

class BusinessResearcher:
    """
    商业研究员智能体类。
    
    核心职责：
        1. 从 BP 中提取搜索关键词；
        2. 调度联网搜索获取市场情报；
        3. 将 BP 内容与搜索结果喂给 LLM，产出深度分析报告。
    
    属性:
        api_key (str): LLM 的授权密钥。
        client (OpenAI): OpenAI 客户端实例（配置 DeepSeek 的 base_url）。
    """

    def __init__(self, api_key: str):
        """
        初始化 BusinessResearcher 类。

        参数:
            api_key (str): LLM 的授权密钥。
        
        执行流:
            1. 保存 API Key 到实例变量；
            2. 创建 OpenAI Client，指定 base_url 为 DeepSeek 的端点。
        
        为什么要单独设置 base_url？
            因为 OpenAI 库默认连接 OpenAI 官方服务器。DeepSeek 兼容 OpenAI 的 
            API 格式，但需要修改请求地址。这种设计叫"接口兼容"——相同的代码，
            只需改配置就能切换不同的 LLM 服务商。
        """
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    def _get_search_keywords(self, bp_text: str) -> List[str]:
        """
        私有方法：利用 LLM 从商业计划书（BP）文本中分析并提取 3 个核心搜索关键词。

        参数:
            bp_text (str): 商业计划书的文本内容（建议前 2000 字）。

        返回:
            List[str]: 包含 3 个字符串的列表，如 ["市场规模", "竞争对手", "技术趋势"]。
        
        执行流:
            1. 截取 BP 前 2000 字（防止上下文溢出）；
            2. 构造精准的提取型 Prompt；
            3. 调用 LLM，模式为单轮对话（不需要历史记忆）；
            4. 解析返回字符串，按逗号分割成列表。
        
        为什么要限制字符数？
            LLM 的上下文窗口是有成本的。对于提取关键词这种轻量任务，
            前 2000 字已经包含核心商业模式信息，全文输入会浪费 Token。
        """
        # 截取前 20000 字
        bp_snippet = bp_text[:20000]
        
        prompt = (
            "请阅读以下商业计划书片段，提取 3 个最核心的搜索关键词，"
            "用于在 Google 查找该项目的竞品和市场规模。"
            "仅返回关键词，用逗号分隔，不要说废话。\n\n"
            f"商业计划书片段：\n{bp_snippet}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3  # 降低随机性，确保输出稳定
            )
            # 提取 LLM 返回的文本
            keywords_text = response.choices[0].message.content.strip()
            # 按逗号分割成列表
            keywords = [k.strip() for k in keywords_text.split(',')]
            return keywords[:3]  # 保证只取前 3 个
        except Exception as e:
            print(f"[ERROR] 提取关键词失败: {e}")
            traceback.print_exc()
            return ["市场规模", "竞品分析", "行业趋势"]  # 兜底策略

    def analyze_business_potential(self, pdf_path: str) -> Dict:
        """
        项目主入口方法：执行完整的商业潜力分析逻辑。

        流程步骤:
            1. 调用 utils.extract_text_from_pdf 读取 PDF 内容。
            2. 调用 self._get_search_keywords 提取 3 个搜索关键词。
            3. 循环调用 utils.google_search 获取每个关键词的联网搜索结果。
            4. 构建最终 Prompt，将 BP 内容和搜索结果合并。
            5. 调用 LLM 获取深度分析。
            6. 调用 utils.clean_json_string 清洗结果并转化为字典输出。

        参数:
            pdf_path (str): 待分析的 BP 文件路径。

        返回:
            Dict: 包含分析结论、风险评估、市场机会等字段的结构化字典。
        
        异常处理策略:
            在 NLP 应用中，外部依赖（API 调用、网络请求）经常会失败。
            我们使用 try...except 捕获所有异常，并返回带有 'error' 字段的
            字典，确保程序不会因为一次失败就崩溃。
        """
        try:
            # 步骤 1: 提取 PDF 文本
            print(f"[INFO] 正在读取 PDF: {pdf_path}")
            bp_full_text = utils.extract_text_from_pdf(pdf_path)
            
            if "失败" in bp_full_text:
                return {"error": f"PDF 读取失败: {bp_full_text}"}
            
            # 步骤 2: 提取搜索关键词
            print("[INFO] 正在提取搜索关键词...")
            keywords = self._get_search_keywords(bp_full_text)
            print(f"[INFO] 提取到的关键词: {keywords}")
            
            # 步骤 3: 联网搜索
            search_results = []
            for keyword in keywords:
                print(f"[INFO] 正在搜索: {keyword}")
                result = utils.google_search(keyword)
                search_results.append(f"=== 关键词: {keyword} ===\n{result}\n")
            
            search_context = "\n".join(search_results)
            
            # 步骤 4: 准备数据（截取 BP 前 5000 字）
            bp_summary = bp_full_text[:5000]
            
            # 步骤 5: 构造最终 Prompt
            user_message = (
                f"商业计划书内容:\n{bp_summary}\n\n"
                f"互联网搜索情报:\n{search_context}"
            )
            
            messages = [
                {"role": "system", "content": config.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
            
            # 步骤 6: 调用 LLM 进行深度分析
            print("[INFO] 正在调用 LLM 进行深度分析...")
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.5  # 保持适度创造性
            )
            
            raw_output = response.choices[0].message.content
            print(f"[DEBUG] LLM 原始输出:\n{raw_output}\n")
            
            # 步骤 7: 清洗并解析 JSON
            clean_json = utils.clean_json_string(raw_output)
            result = json.loads(clean_json)
            
            print("[SUCCESS] 分析完成！")
            return result
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON 解析失败: {str(e)}\n原始输出: {raw_output}"
            print(f"[ERROR] {error_msg}")
            return {"error": error_msg}
        
        except Exception as e:
            error_msg = f"分析流程异常: {str(e)}\n详细信息:\n{traceback.format_exc()}"
            print(f"[ERROR] {error_msg}")
            return {"error": error_msg}
