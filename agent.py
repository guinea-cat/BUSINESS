"""
agent.py
商业分析智能体核心模块。
负责协调 PDF 解析、赛道识别、联网搜索及全领域 VC 视角深度分析。
"""

import json
import logging
import traceback
from typing import List, Dict
from openai import OpenAI
import config
import utils

# 配置日志
logger = logging.getLogger(__name__)

class BusinessResearcher:
    """
    商业研究员智能体，模拟 VC 合伙人进行项目评审。
    """

    def __init__(self, api_key: str):
        """
        初始化智能体。
        
        参数:
            api_key (str): LLM 授权密钥。
        """
        self.api_key = api_key
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.LLM_BASE_URL
        )

    def _detect_industry(self, bp_text: str) -> str:
        """
        第一阶段：识别项目细分赛道。
        
        参数:
            bp_text (str): BP 全文。
            
        返回:
            str: 识别出的赛道名称。
        """
        bp_snippet = bp_text[:3000]
        prompt = (
            "你是一名全领域 VC 合伙人，擅长快速识别创业项目所属的细分赛道。\n\n"
            "### 任务\n"
            "阅读以下商业计划书摘要，识别该项目属于哪个**细分赛道**。\n\n"
            "### 输出格式\n"
            "用 '大赛道 - 小赛道' 的格式返回，如：'智慧医疗 - AI 辅助诊断'。\n"
            "仅返回赛道名称，不要说废话。\n\n"
            f"商业计划书摘要：\n{bp_snippet}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            industry = response.choices[0].message.content.strip()
            logger.info(f"识别到赛道: {industry}")
            return industry
        except Exception as e:
            logger.error(f"赛道识别失败: {e}")
            return "全领域赛道"

    def _get_search_keywords(self, bp_text: str, detected_industry: str) -> List[str]:
        """
        第二阶段：基于赛道生成精准搜索关键词。
        
        参数:
            bp_text (str): BP 文本。
            detected_industry (str): 识别出的赛道。
        """
        bp_snippet = bp_text[:20000]
        prompt = (
            "你是一名资深的商业情报分析师，擅长从商业计划书中提取高质量的搜索关键词。\n\n"
            f"项目赛道：**{detected_industry}**\n"
            "提取 4-5 个搜索关键词，用于在 Google 查找该赛道的市场数据、融资信息和竞品情况。\n\n"
            "### 策略要求\n"
            "1. 宏观行业词：查询市场规模、CAGR、融资报告。\n"
            "2. 微观对手词：查询行业龙头、替代方案。如果赛道较新，必须搜索其上位赛道的巨头玩家。\n\n"
            "### 输出格式\n"
            "仅返回关键词，用英文逗号分隔。\n\n"
            f"商业计划书片段：\n{bp_snippet}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            keywords_text = response.choices[0].message.content.strip()
            keywords = [k.strip() for k in keywords_text.split(',')]
            return keywords[:5]
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return [f"{detected_industry} 市场报告", f"{detected_industry} 竞品"]

    def analyze_bp_pipeline(self, pdf_path: str) -> Dict:
        """
        全流程商业分析流水线。
        
        参数:
            pdf_path (str): PDF 文件路径。
            
        返回:
            Dict: 格式化的商业分析 JSON 报告。
        """
        try:
            # 1. 文本提取
            logger.info(f"开启流水线分析，处理文件: {pdf_path}")
            bp_full_text = utils.extract_text_from_pdf(pdf_path)
            if "失败" in bp_full_text:
                return {"error": "PDF 内容无法读取"}

            # 2. 赛道感知
            detected_industry = self._detect_industry(bp_full_text)
            
            # 3. 关键词获取
            keywords = self._get_search_keywords(bp_full_text, detected_industry)
            
            # 4. 联网检索
            search_context = ""
            for kw in keywords:
                result = utils.google_search(kw)
                search_context += f"--- 关键词: {kw} ---\n{result}\n"

            # 5. LLM 深度分析
            logger.info("发起 LLM 深度分析...")
            bp_summary = bp_full_text[:5000]
            messages = [
                {"role": "system", "content": config.SYSTEM_PROMPT},
                {"role": "user", "content": f"BP 摘要内容:\n{bp_summary}\n\n外部搜索情报:\n{search_context}"}
            ]
            
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=0.5
            )
            
            raw_output = response.choices[0].message.content
            clean_json = utils.clean_json_string(raw_output)
            result = json.loads(clean_json)

            # 6. JSON 完整性校验与兜底
            required_keys = ["project_identity", "industry_analysis", "competitors", "funding_ecosystem", "pain_point_validation", "public_sentiment", "risk_assessment"]
            for key in required_keys:
                if key not in result:
                    logger.warning(f"字段 {key} 缺失，正在进行默认填充。")
                    if key == "project_identity":
                        result[key] = {
                            "project_name": "Unknown Project",
                            "slogan": "N/A",
                            "elevator_pitch": "未能从 BP 中提取有效简介",
                            "stage": "未知"
                        }
                    elif key == "industry_analysis":
                        result[key] = {"detected_industry": detected_industry, "market_size": "Not Found", "cagr": "Not Found", "source": "N/A"}
                    elif key == "competitors": result[key] = []
                    elif key == "funding_ecosystem": result[key] = {"heat_level": "Unknown", "trend_summary": "Not Found"}
                    elif key == "pain_point_validation": result[key] = {"score": 0, "reason": "N/A"}
                    elif key == "public_sentiment": result[key] = {"label": "Neutral", "summary": "Not Found"}
                    elif key == "risk_assessment": result[key] = ["识别风险失败"]

            logger.info("分析流程圆满完成。")
            return result

        except Exception as e:
            logger.error(f"分析流水线崩溃: {e}\n{traceback.format_exc()}")
            return {
                "error": "Pipeline Failure",
                "details": str(e),
                "template": {
                    "industry_analysis": {"detected_industry": "Error", "market_size": "Not Found", "cagr": "Not Found", "source": "N/A"},
                    "competitors": [],
                    "funding_ecosystem": {"heat_level": "Unknown", "trend_summary": "N/A"},
                    "pain_point_validation": {"score": 0, "reason": "N/A"},
                    "public_sentiment": {"label": "Neutral", "summary": "N/A"},
                    "risk_assessment": ["内部系统异常"]
                }
            }
