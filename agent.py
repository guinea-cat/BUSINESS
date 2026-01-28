"""
agent.py
商业分析智能体核心模块。
负责协调 PDF 解析、赛道识别、联网搜索及全领域 VC 视角深度分析。
优化版：搜索模块并发执行，大幅缩短总体分析时间。
"""

import json
import logging
import traceback
from typing import List, Dict
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        
        # 视觉专用客户端 (解决 400 错误：解耦多模态与文本请求)
        vision_api_key = getattr(config, "VISION_API_KEY", api_key)
        vision_base_url = getattr(config, "VISION_BASE_URL", config.LLM_BASE_URL)
        
        # 如果视觉配置与文本配置一致且为 DeepSeek，则会有兼容性风险
        # 建议用户在 config.py 中明确配置 VISION_BASE_URL 为支持 Vision 的端点
        self.vision_client = OpenAI(
            api_key=vision_api_key,
            base_url=vision_base_url,
            timeout=120.0  # 增加超时限制，适应代理环境下的图片上传
        )

    def _detect_industry(self, bp_text: str) -> str:
        """
        第一阶段：识别项目细分赛道。
        
        参数:
            bp_text (str): BP 全文（可包含图表描述的增强文本）。
            
        返回:
            str: 识别出的赛道名称。
        """
        bp_snippet = bp_text[:20000]
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
        第二阶段：基于赛道生成中英文双语搜索关键词。
        
        参数:
            bp_text (str): BP 文本（可包含图表描述的增强文本）。
            detected_industry (str): 识别出的赛道。
        """
        bp_snippet = bp_text[:30000]
        prompt = (
            "你是一名资深的商业情报分析师，擅长从商业计划书中提取高质量的中英文双语搜索关键词。\n\n"
            f"项目赛道：**{detected_industry}**\n"
            "### 任务\n"
            "提取 10 个精准搜索关键词（5 个中文，5 个英文），用于在 Google 查找全球市场数据、国际竞品和商业模式趋势。\n\n"
            "### 策略要求：\n"
            "1. **中文关键词**：覆盖国内市场规模、政策环境、本土竞品分析。\n"
            "2. **英文关键词**：覆盖全球行业报告（Global Market Report）、海外巨头动态（Leading Players）、国际融资趋势（Funding Trends）。\n"
            "3. **必须包含模式变体**：例如 \"{Industry} market size\"、\"{Competitor} revenue\"、\"{Industry} failure cases\"。\n\n"
            "### 输出格式\n"
            "仅返回关键词，用英文逗号分隔。不要有任何解释。\n\n"
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
            return keywords[:10]
        except Exception as e:
            logger.error(f"提取双语关键词失败: {e}")
            return [
                f"{detected_industry} 市场规模", 
                f"{detected_industry} market size",
                f"{detected_industry} competitors analysis",
                f"{detected_industry} 商业模式",
                f"{detected_industry} business model",
                f"{detected_industry} global trends"
            ]

    def _concurrent_search(self, keywords: List[str]) -> Dict[str, str]:
        """
        并发执行 Google 搜索（性能优化关键点）。
        
        参数:
            keywords: 搜索关键词列表
            
        返回:
            Dict[关键词, 搜索结果]
        """
        search_results = {}
        
        def search_worker(kw: str, idx: int):
            """单个搜索任务"""
            start_id = idx * 5 + 1  # 每个关键词搜索 5 条，ID 依次累加
            result = utils.google_search(kw, start_id=start_id)
            return (kw, result)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(search_worker, kw, i): kw 
                for i, kw in enumerate(keywords)
            }
            
            for future in as_completed(futures):
                kw, result = future.result()
                if result:
                    search_results[kw] = result
        
        logger.info(f"并发搜索完成：{len(search_results)}/{len(keywords)} 个关键词获得结果")
        return search_results

    def _generate_basic_info(self, fusion_context: str) -> Dict:
        """
        【并发子任务 1】生成基础信息组：project_identity, industry_analysis, business_analysis
        
        原理：这 3 个字段主要来自 BP 内容本身，无需复杂推理，可以快速生成。
        
        参数：
            fusion_context (str): 融合后的上下文（BP 内容 + 搜索结果）
        
        返回：
            Dict: 包含 3 个字段的 JSON 字典
        """
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": config.PROMPT_IDENTITY_BUSINESS},
                    {"role": "user", "content": fusion_context}
                ],
                temperature=0.3
            )
            raw_output = response.choices[0].message.content
            clean_json = utils.clean_json_string(raw_output)
            # 使用 repair_json 修复可能的截断问题
            repaired_json = utils.repair_json(clean_json)
            return json.loads(repaired_json)
        except Exception as e:
            logger.error(f"生成基础信息组失败: {e}")
            return {}

    def _generate_external_intel(self, fusion_context: str) -> Dict:
        """
        【并发子任务 2】生成外部情报组：competitors, funding_ecosystem, public_sentiment, raw_evidence
        
        原理：这 4 个字段主要基于联网搜索结果，关注外部市场情报。
        
        参数：
            fusion_context (str): 融合后的上下文（BP 内容 + 搜索结果）
        
        返回：
            Dict: 包含 4 个字段的 JSON 字典
        """
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": config.PROMPT_MARKET_COMPETITION},
                    {"role": "user", "content": fusion_context}
                ],
                temperature=0.3
            )
            raw_output = response.choices[0].message.content
            clean_json = utils.clean_json_string(raw_output)
            # 使用 repair_json 修复可能的截断问题
            repaired_json = utils.repair_json(clean_json)
            return json.loads(repaired_json)
        except Exception as e:
            logger.error(f"生成外部情报组失败: {e}")
            return {}

    def _generate_valuation(self, fusion_context: str) -> Dict:
        """
        【并发子任务 3】生成估值模型：valuation_model
        
        原理：专注于量化评分，将复杂的评估任务拆分为独立的并发任务。
        
        参数：
            fusion_context (str): 融合后的上下文（BP 内容 + 搜索结果）
        
        返回：
            Dict: 包含 valuation_model 字段的 JSON 字典
        """
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": config.PROMPT_VALUATION},
                    {"role": "user", "content": fusion_context}
                ],
                temperature=0.3
            )
            raw_output = response.choices[0].message.content
            clean_json = utils.clean_json_string(raw_output)
            # 使用 repair_json 修复可能的截断问题
            repaired_json = utils.repair_json(clean_json)
            return json.loads(repaired_json)
        except Exception as e:
            logger.error(f"生成估值模型失败: {e}")
            return {}

    def _generate_risks_and_qa(self, fusion_context: str) -> Dict:
        """
        【并发子任务 4】生成风险评估与拷问：vc_grill, pain_point_validation, risk_assessment
        
        原理：专注于风险识别和尖锐提问，减轻单个任务的负担。
        
        参数：
            fusion_context (str): 融合后的上下文（BP 内容 + 搜索结果）
        
        返回：
            Dict: 包含 3 个字段的 JSON 字典
        """
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": config.PROMPT_RISK_QA},
                    {"role": "user", "content": fusion_context}
                ],
                temperature=0.3
            )
            raw_output = response.choices[0].message.content
            clean_json = utils.clean_json_string(raw_output)
            # 使用 repair_json 修复可能的截断问题
            repaired_json = utils.repair_json(clean_json)
            return json.loads(repaired_json)
        except Exception as e:
            logger.error(f"生成风险评估组失败: {e}")
            return {}

    def analyze_bp_pipeline(self, pdf_path: str) -> Dict:
        """
        全流程商业分析流水线（升级版：视觉信息前置融合，确保图片型 PDF 分析有效性）。
        
        参数:
            pdf_path (str): PDF 文件路径。
            
        返回:
            Dict: 格式化的商业分析 JSON 报告。
        """
        try:
            # 1. 文本与图像提取
            logger.info(f"开启流水线分析（多模态+并发优化），处理文件: {pdf_path}")
            pdf_content = utils.extract_content_from_pdf(pdf_path)
            bp_full_text = pdf_content["text"]
            bp_images = pdf_content["images"]
            
            if "失败" in bp_full_text:
                return {"error": "PDF 内容无法读取"}

            # 2. 视觉内容解析（前置到赛道识别之前，关键修复点）
            visual_descriptions = ""
            if bp_images:
                logger.info(f"检测到 {len(bp_images)} 张有效图片，正在发起并发视觉分析...")
                visual_descriptions = utils.describe_visual_elements(self.vision_client, bp_images)
                logger.info(f"视觉分析完成，提取了 {len(visual_descriptions)} 字符的图表描述")

            # 2.5 创建增强文本（核心修复：融合原文本与视觉描述）
            enhanced_text = bp_full_text
            if visual_descriptions and visual_descriptions != "未发现显著视觉元素。":
                logger.info("正在融合文本与视觉信息，生成增强分析上下文...")
                enhanced_text = f"{bp_full_text}\n\n{visual_descriptions}"
            else:
                logger.warning("未检测到有效视觉内容，仅使用纯文本进行分析")

            # 3. 赛道感知（现在基于增强文本，图片型 PDF 也能准确识别）
            detected_industry = self._detect_industry(enhanced_text)
            
            # 4. 关键词获取（现在基于增强文本，关键词更精准）
            keywords = self._get_search_keywords(enhanced_text, detected_industry)
            
            # 5. 并发联网检索（性能优化关键点）
            logger.info("正在并发执行 Google 搜索...")
            search_results = self._concurrent_search(keywords)
            
            # 组装搜索上下文
            search_context = ""
            for kw, result in search_results.items():
                search_context += f"--- 关键词: {kw} ---\n{result}\n"

            # 6. 并发 JSON 生成（性能优化关键点：将长文本生成拆分为 4 个子任务）
            logger.info("发起并发 JSON 生成（4 个子任务）...")
            bp_summary = enhanced_text[:30000]  # 使用增强文本而非原始文本
            fusion_context = (
                f"### 📄 商业计划书内容摘要（包含文本与图表解析）\n{bp_summary}\n\n"
                f"### 🔍 外部搜索情报\n{search_context}"
            )
            
            # 并发调用 4 个生成方法（Map-Reduce 模式）
            result = {}
            with ThreadPoolExecutor(max_workers=4) as executor:
                # 提交 4 个并发任务
                future_basic = executor.submit(self._generate_basic_info, fusion_context)
                future_intel = executor.submit(self._generate_external_intel, fusion_context)
                future_valuation = executor.submit(self._generate_valuation, fusion_context)
                future_risks = executor.submit(self._generate_risks_and_qa, fusion_context)
                
                # 等待所有任务完成并合并结果
                basic_info = future_basic.result()
                external_intel = future_intel.result()
                valuation_data = future_valuation.result()
                risks_qa_data = future_risks.result()
                
                # 合并 4 个字典
                result.update(basic_info)
                result.update(external_intel)
                result.update(valuation_data)
                result.update(risks_qa_data)
            
            logger.info("并发 JSON 生成完成，正在校验完整性...")

            # 7. JSON 完整性校验与兜底（新增 valuation_model）
            required_keys = ["project_identity", "industry_analysis", "business_analysis", "competitors", "raw_evidence", "vc_grill", "valuation_model", "funding_ecosystem", "pain_point_validation", "public_sentiment", "risk_assessment"]
            for key in required_keys:
                if key not in result:
                    logger.warning(f"字段 {key} 缺失，正在进行默认填充。")
                    if key == "project_identity":
                        result[key] = {
                            "project_name": "Unknown Project",
                            "slogan": "N/A",
                            "description": "未能从 BP 中提取深度描述",
                            "revenue_model": "N/A",
                            "team_background": "Not Mentioned",
                            "stage": "未知"
                        }
                    elif key == "industry_analysis":
                        result[key] = {"detected_industry": detected_industry, "market_size": "Not Found", "cagr": "Not Found", "source": "N/A"}
                    elif key == "business_analysis":
                        result[key] = {"business_model_critique": "N/A", "technical_moat": "N/A"}
                    elif key == "competitors": result[key] = []
                    elif key == "raw_evidence": result[key] = []
                    elif key == "vc_grill": result[key] = []
                    elif key == "valuation_model":
                        result[key] = {
                            "total_score": 50,
                            "rating": "C",
                            "summary": "数据严重不足，无法进行全面量化评估",
                            "dimensions": {
                                "market": {
                                    "score": 10,
                                    "max_score": 20,
                                    "analysis": "缺乏市场规模与增长数据",
                                    "sub_scores": {"market_size": 5, "timing_growth": 5}
                                },
                                "product": {
                                    "score": 10,
                                    "max_score": 25,
                                    "analysis": "未能识别核心技术壁垒与创新点",
                                    "sub_scores": {"uniqueness": 5, "moat": 5}
                                },
                                "business_model": {
                                    "score": 10,
                                    "max_score": 20,
                                    "analysis": "商业模式与盈利路径不明确",
                                    "sub_scores": {"profitability": 5, "scalability": 5}
                                },
                                "team": {
                                    "score": 10,
                                    "max_score": 25,
                                    "analysis": "BP 中未提及核心团队背景",
                                    "sub_scores": {"founder_capability": 5, "completeness": 5}
                                },
                                "execution": {
                                    "score": 10,
                                    "max_score": 10,
                                    "analysis": "缺乏业务验证与合规风险评估依据",
                                    "sub_scores": {"traction": 5, "risk_safety": 5}
                                }
                            }
                        }
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
