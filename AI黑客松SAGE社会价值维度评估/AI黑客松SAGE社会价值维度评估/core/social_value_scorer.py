"""社会价值评估评分引擎（AI黑客松比赛专用）

全新评估框架：
- 基础项（30%）：伦理安全合规性 - 必须评估的部分
- 加分项（70%）：社会影响、环境友好、公益导向、长期愿景 - 根据项目特点选择性突出

特点：
- 注重项目的社会价值贡献
- 识别潜在的社会风险
- 为评委提供全面的社会价值分析
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import time
import re

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import DEFAULT_WEIGHTS, SOCIAL_VALUE_LEVELS

from .github_fetcher import GitHubFetcher, RepoInfo
from .report_optimizer import ReportOptimizer
from .report_quality import ReportQualityEvaluator
from .prompt_engineering import get_prompt_library


@dataclass
class DimensionScore:
    """单个维度得分"""
    name: str
    name_cn: str
    score: float  # 原始得分 0-100
    weight: float  # 权重 0-100
    weighted_score: float  # 加权得分
    details: str  # 详细说明
    category: str = ""  # 所属大类：basic 或 bonus


@dataclass
class SocialValueReport:
    """社会价值评估报告"""
    repo_name: str
    repo_url: str
    
    # 总分和等级
    total_score: float
    level: str
    level_stars: str
    
    # 核心信息
    core_value_summary: str = ""  # 项目是什么及核心价值
    social_value_type: str = ""  # 社会价值类型
    
    # 两大板块得分
    basic_items_score: float = 0.0  # 基础项总分（满分30）
    bonus_items_score: float = 0.0  # 加分项总分（满分70）
    
    # 7个子维度得分
    dimensions: List[DimensionScore] = field(default_factory=list)
    
    # 仓库元信息
    stars: int = 0
    language: str = ""
    description: str = ""
    
    # 分析时间
    analysis_time: float = 0.0
    
    # 详细维度分析
    dimension_analyses: Dict[str, str] = field(default_factory=dict)
    
    # 社会价值亮点
    social_value_highlights: List[str] = field(default_factory=list)
    
    # 改进建议
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # 评委关注点
    judge_focus_points: List[str] = field(default_factory=list)
    
    # 评估置信度
    confidence_level: str = "中"
    information_sufficiency: str = "中"
    
    # 核心社会价值类型
    core_social_value_types: List[str] = field(default_factory=list)


class SocialValueScorer:
    """社会价值评估评分引擎
    
    新版7维度框架：
    - 基础项（30%）：伦理安全合规性
      - 伦理红线检查 (10%)
      - 隐私与数据保护 (10%)
      - 算法公平性意识 (10%)
    - 加分项（70%）：社会价值亮点
      - 社会影响深度 (25%)
      - 环境可持续性 (15%)
      - 公益普惠导向 (15%)
      - 长期愿景与变革潜力 (15%)
    """
    
    # 维度名称映射
    DIMENSION_NAMES = {
        "ethics_redline": "伦理红线检查",
        "privacy_protection": "隐私与数据保护",
        "algorithm_fairness": "算法公平性意识",
        "social_impact": "社会影响深度",
        "environmental_friendliness": "环境可持续性",
        "charity_orientation": "公益普惠导向",
        "long_term_vision": "长期愿景与变革潜力",
    }
    
    # 社会价值关键词
    SOCIAL_VALUE_KEYWORDS = {
        "social_impact": ["医疗", "健康", "教育", "养老", "残障", "无障碍", "弱势群体", "社会问题", "community", "health", "education", "elderly", "disability", "vulnerable"],
        "environmental": ["环保", "可持续", "绿色", "气候", "低碳", "碳中和", "environment", "sustainable", "green", "climate"],
        "charity": ["公益", "慈善", "非营利", "普惠", "accessibility", "charity", "nonprofit", "public good"],
        "vision": ["长期", "愿景", "变革", "未来", "sustainable", "vision", "future", "transformation"],
    }
    
    # 伦理风险关键词
    ETHICS_RISK_KEYWORDS = {
        "surveillance": ["监控", "surveillance", "monitoring", "tracking"],
        "discrimination": ["歧视", "偏见", "bias", "discrimination"],
        "harm": ["危害", "伤害", "harm", "danger"],
        "deception": ["欺骗", "操纵", "deception", "manipulation"],
        "privacy": ["隐私", "数据收集", "data collection", "privacy"],
    }
    
    def __init__(self, github_token: str = None, use_deepseek: bool = True):
        """初始化评分引擎
        
        Args:
            github_token: GitHub API Token
            use_deepseek: 是否使用DeepSeek模型优化报告
        """
        self.github_fetcher = GitHubFetcher(token=github_token)
        
        # 初始化报告优化器
        self.report_optimizer = None
        self.use_deepseek = use_deepseek
        if use_deepseek:
            try:
                self.report_optimizer = ReportOptimizer()
            except Exception as e:
                print(f"Warning: Failed to init ReportOptimizer: {e}")
        
        # 初始化提示词工程库
        self.prompt_library = get_prompt_library()
        
        # 初始化报告质量评估器
        self.quality_evaluator = ReportQualityEvaluator()
    
    def _get_level(self, score: float) -> tuple:
        """根据分数获取等级"""
        for (low, high), (level, stars) in SOCIAL_VALUE_LEVELS.items():
            if low <= score <= high:
                return level, stars
        return "社会价值有限", "⭐"
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """归一化权重"""
        total = sum(weights.values())
        if total == 0:
            return DEFAULT_WEIGHTS.copy()
        return {k: v * 100 / total for k, v in weights.items()}
    
    def _detect_keywords(self, text: str, keywords_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """检测关键词"""
        text_lower = text.lower()
        detected = {}
        for category, keywords in keywords_dict.items():
            found = [kw for kw in keywords if kw in text_lower]
            if found:
                detected[category] = found
        return detected
    
    def _evaluate_ethics_redline(self, repo_info: RepoInfo) -> Dict[str, Any]:
        """评估伦理红线检查"""
        full_text = f"{repo_info.description} {repo_info.readme_content}"
        risk_keywords = self._detect_keywords(full_text, self.ETHICS_RISK_KEYWORDS)
        
        score = 80  # 基础分
        analysis_parts = []
        risk_level = "安全"
        
        # 严重风险检查
        if risk_keywords.get("surveillance"):
            score -= 30
            analysis_parts.append("项目可能涉及监控功能，需关注用户隐私保护")
            risk_level = "需关注"
        if risk_keywords.get("discrimination"):
            score -= 25
            analysis_parts.append("项目可能存在潜在的歧视风险，需加强公平性设计")
            risk_level = "需关注"
        if risk_keywords.get("harm"):
            score -= 40
            analysis_parts.append("项目可能被用于造成伤害，存在严重伦理风险")
            risk_level = "危险"
        if risk_keywords.get("deception"):
            score -= 20
            analysis_parts.append("项目可能存在欺骗性设计，需加强透明度")
            risk_level = "需关注"
        
        if not risk_keywords:
            analysis_parts.append("未发现明显的伦理风险，项目设计符合基本伦理要求")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "risk_level": risk_level,
            "analysis": "；".join(analysis_parts) if analysis_parts else "伦理风险评估数据不足",
            "detected_risks": list(risk_keywords.keys()),
        }
    
    def _evaluate_privacy_protection(self, repo_info: RepoInfo) -> Dict[str, Any]:
        """评估隐私与数据保护"""
        full_text = f"{repo_info.description} {repo_info.readme_content}"
        
        score = 70  # 基础分
        analysis_parts = []
        compliance_level = "基本符合"
        
        # 隐私保护相关关键词
        privacy_keywords = ["隐私", "数据保护", "privacy", "data protection", "consent", "同意"]
        found_privacy = any(kw in full_text.lower() for kw in privacy_keywords)
        
        if found_privacy:
            score += 15
            analysis_parts.append("项目提及了隐私保护相关内容")
        else:
            analysis_parts.append("项目未明确提及隐私保护措施，建议加强")
        
        # 数据收集相关内容
        data_collection_keywords = ["数据收集", "用户数据", "data collection", "user data"]
        found_collection = any(kw in full_text.lower() for kw in data_collection_keywords)
        
        if found_collection:
            analysis_parts.append("项目涉及数据收集，需确保合规性")
        
        # 开源许可检查
        license_name = getattr(repo_info, 'license_name', '')
        if license_name:
            score += 10
            analysis_parts.append(f"项目使用{license_name}开源许可，有利于透明度")
        
        score = max(0, min(100, score))
        
        if score >= 90:
            compliance_level = "符合"
        elif score < 60:
            compliance_level = "不符合"
        
        return {
            "score": score,
            "compliance_level": compliance_level,
            "analysis": "；".join(analysis_parts) if analysis_parts else "隐私保护评估数据不足",
        }
    
    def _evaluate_algorithm_fairness(self, repo_info: RepoInfo) -> Dict[str, Any]:
        """评估算法公平性意识"""
        full_text = f"{repo_info.description} {repo_info.readme_content}"
        
        score = 60  # 基础分
        analysis_parts = []
        awareness_level = "基本意识"
        
        # 公平性相关关键词
        fairness_keywords = ["公平", "bias", "歧视", "fairness", "equity", "inclusion"]
        found_fairness = any(kw in full_text.lower() for kw in fairness_keywords)
        
        if found_fairness:
            score += 25
            analysis_parts.append("项目考虑了算法公平性问题")
            awareness_level = "高度自觉"
        else:
            analysis_parts.append("项目未明确提及算法公平性，建议加强考虑")
        
        # 多样性相关内容
        diversity_keywords = ["多样性", "inclusion", "包容性", "diversity"]
        found_diversity = any(kw in full_text.lower() for kw in diversity_keywords)
        
        if found_diversity:
            score += 10
            analysis_parts.append("项目关注多样性和包容性")
        
        score = max(0, min(100, score))
        
        if score < 50:
            awareness_level = "缺乏考虑"
        
        return {
            "score": score,
            "awareness_level": awareness_level,
            "analysis": "；".join(analysis_parts) if analysis_parts else "算法公平性评估数据不足",
        }
    
    def _evaluate_social_impact(self, repo_info: RepoInfo) -> Dict[str, Any]:
        """评估社会影响深度"""
        full_text = f"{repo_info.description} {repo_info.readme_content}"
        social_keywords = self._detect_keywords(full_text, self.SOCIAL_VALUE_KEYWORDS)
        
        score = 50  # 基础分
        analysis_parts = []
        impact_level = "中"
        
        # 社会影响相关关键词
        if social_keywords.get("social_impact"):
            score += 25
            analysis_parts.append("项目关注社会问题，具有潜在的社会影响")
            impact_level = "高"
        
        # 特定群体服务
        specific_groups = ["老人", "儿童", "残障", "弱势群体", "elderly", "children", "disabled", "vulnerable"]
        found_specific = any(kw in full_text.lower() for kw in specific_groups)
        
        if found_specific:
            score += 15
            analysis_parts.append("项目关注特定弱势群体，体现社会关怀")
        
        # 问题解决针对性
        problem_keywords = ["解决", "问题", "solution", "solve", "address"]
        found_problem = any(kw in full_text.lower() for kw in problem_keywords)
        
        if found_problem:
            score += 10
            analysis_parts.append("项目旨在解决具体社会问题")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "impact_level": impact_level,
            "analysis": "；".join(analysis_parts) if analysis_parts else "社会影响评估数据不足",
            "detected_areas": list(social_keywords.get("social_impact", [])),
        }
    
    def _evaluate_environmental_friendliness(self, repo_info: RepoInfo) -> Dict[str, Any]:
        """评估环境可持续性"""
        full_text = f"{repo_info.description} {repo_info.readme_content}"
        social_keywords = self._detect_keywords(full_text, self.SOCIAL_VALUE_KEYWORDS)
        
        score = 40  # 基础分
        analysis_parts = []
        green_level = "低"
        
        # 环境相关关键词
        if social_keywords.get("environmental"):
            score += 35
            analysis_parts.append("项目关注环境保护，具有环境友好性")
            green_level = "高"
        
        # 可持续发展相关内容
        sustainability_keywords = ["可持续", "sustainable", "绿色", "green", "低碳", "low carbon"]
        found_sustainability = any(kw in full_text.lower() for kw in sustainability_keywords)
        
        if found_sustainability:
            score += 15
            analysis_parts.append("项目体现可持续发展理念")
        
        # 资源节约相关内容
        resource_keywords = ["节能", "减排", "资源节约", "energy saving", "resource efficiency"]
        found_resource = any(kw in full_text.lower() for kw in resource_keywords)
        
        if found_resource:
            score += 10
            analysis_parts.append("项目关注资源节约")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "green_level": green_level,
            "analysis": "；".join(analysis_parts) if analysis_parts else "环境可持续性评估数据不足",
        }
    
    def _evaluate_charity_orientation(self, repo_info: RepoInfo) -> Dict[str, Any]:
        """评估公益普惠导向"""
        full_text = f"{repo_info.description} {repo_info.readme_content}"
        social_keywords = self._detect_keywords(full_text, self.SOCIAL_VALUE_KEYWORDS)
        
        score = 45  # 基础分
        analysis_parts = []
        charity_level = "中"
        
        # 公益相关关键词
        if social_keywords.get("charity"):
            score += 30
            analysis_parts.append("项目具有公益导向，关注社会福祉")
            charity_level = "高"
        
        # 普惠性相关内容
        accessibility_keywords = ["普惠", "无障碍", "accessibility", "inclusive", "affordable"]
        found_accessibility = any(kw in full_text.lower() for kw in accessibility_keywords)
        
        if found_accessibility:
            score += 15
            analysis_parts.append("项目关注普惠性和可及性")
        
        # 非营利相关内容
        nonprofit_keywords = ["非营利", "nonprofit", "慈善", "charity", "公益", "public good"]
        found_nonprofit = any(kw in full_text.lower() for kw in nonprofit_keywords)
        
        if found_nonprofit:
            score += 10
            analysis_parts.append("项目体现非营利或公益精神")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "charity_level": charity_level,
            "analysis": "；".join(analysis_parts) if analysis_parts else "公益普惠导向评估数据不足",
        }
    
    def _evaluate_long_term_vision(self, repo_info: RepoInfo) -> Dict[str, Any]:
        """评估长期愿景与变革潜力"""
        full_text = f"{repo_info.description} {repo_info.readme_content}"
        social_keywords = self._detect_keywords(full_text, self.SOCIAL_VALUE_KEYWORDS)
        
        score = 50  # 基础分
        analysis_parts = []
        vision_level = "中"
        
        # 愿景相关关键词
        if social_keywords.get("vision"):
            score += 20
            analysis_parts.append("项目具有长期发展愿景")
            vision_level = "高"
        
        # 变革相关内容
        transformation_keywords = ["变革", "创新", "transformation", "innovation", "change"]
        found_transformation = any(kw in full_text.lower() for kw in transformation_keywords)
        
        if found_transformation:
            score += 15
            analysis_parts.append("项目具有变革潜力")
        
        # 系统性解决方案
        system_keywords = ["系统", "生态", "system", "ecosystem", "holistic"]
        found_system = any(kw in full_text.lower() for kw in system_keywords)
        
        if found_system:
            score += 10
            analysis_parts.append("项目提供系统性解决方案")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "vision_level": vision_level,
            "analysis": "；".join(analysis_parts) if analysis_parts else "长期愿景评估数据不足",
        }
    
    def _generate_core_value_summary(self, repo_info: RepoInfo, evaluations: Dict[str, Any]) -> str:
        """生成项目核心价值一句话描述"""
        name = repo_info.name
        desc = repo_info.description or ""
        
        # 检测社会价值类型
        social_value_types = []
        if evaluations.get("social_impact", {}).get("impact_level") == "高":
            social_value_types.append("社会问题解决型")
        if evaluations.get("environmental_friendliness", {}).get("green_level") == "高":
            social_value_types.append("环境友好型")
        if evaluations.get("charity_orientation", {}).get("charity_level") == "高":
            social_value_types.append("公益普惠型")
        if evaluations.get("long_term_vision", {}).get("vision_level") == "高":
            social_value_types.append("愿景引领型")
        
        if social_value_types:
            type_str = "、".join(social_value_types[:2])
            return f"**{name}** 是一个{type_str}的AI项目，{desc[:50]}{'...' if len(desc) > 50 else ''}"
        else:
            return f"**{name}** 是一个AI项目，{desc[:60]}{'...' if len(desc) > 60 else ''}"
    
    def _generate_social_value_types(self, evaluations: Dict[str, Any]) -> List[str]:
        """生成核心社会价值类型"""
        types = []
        if evaluations.get("social_impact", {}).get("impact_level") == "高":
            types.append("社会问题解决型")
        if evaluations.get("environmental_friendliness", {}).get("green_level") == "高":
            types.append("环境友好型")
        if evaluations.get("charity_orientation", {}).get("charity_level") == "高":
            types.append("公益普惠型")
        if evaluations.get("long_term_vision", {}).get("vision_level") == "高":
            types.append("愿景引领型")
        
        # 如果没有高等级类型，选择得分最高的
        if not types:
            bonus_evaluations = {
                "social_impact": evaluations.get("social_impact", {}).get("score", 0),
                "environmental_friendliness": evaluations.get("environmental_friendliness", {}).get("score", 0),
                "charity_orientation": evaluations.get("charity_orientation", {}).get("score", 0),
                "long_term_vision": evaluations.get("long_term_vision", {}).get("score", 0),
            }
            top_type = max(bonus_evaluations, key=bonus_evaluations.get)
            type_map = {
                "social_impact": "社会问题解决型",
                "environmental_friendliness": "环境友好型",
                "charity_orientation": "公益普惠型",
                "long_term_vision": "愿景引领型",
            }
            types.append(type_map.get(top_type, "综合型"))
        
        return types[:2]
    
    def _generate_social_value_highlights(self, evaluations: Dict[str, Any]) -> List[str]:
        """生成社会价值亮点"""
        highlights = []
        
        # 社会影响亮点
        if evaluations.get("social_impact", {}).get("score", 0) >= 70:
            highlights.append("社会影响显著，关注重要社会问题")
        
        # 环境友好亮点
        if evaluations.get("environmental_friendliness", {}).get("score", 0) >= 70:
            highlights.append("环境可持续性强，体现绿色发展理念")
        
        # 公益普惠亮点
        if evaluations.get("charity_orientation", {}).get("score", 0) >= 70:
            highlights.append("公益导向明显，关注社会弱势群体")
        
        # 长期愿景亮点
        if evaluations.get("long_term_vision", {}).get("score", 0) >= 70:
            highlights.append("长期愿景清晰，具有变革潜力")
        
        # 伦理合规亮点
        if evaluations.get("ethics_redline", {}).get("risk_level") == "安全":
            highlights.append("伦理合规性良好，未发现明显风险")
        
        return highlights[:3]
    
    def _generate_improvement_suggestions(self, evaluations: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 伦理安全建议
        if evaluations.get("ethics_redline", {}).get("risk_level") != "安全":
            suggestions.append("加强伦理风险管控，确保项目符合基本伦理要求")
        
        # 隐私保护建议
        if evaluations.get("privacy_protection", {}).get("compliance_level") != "符合":
            suggestions.append("完善隐私保护措施，明确数据收集和使用规范")
        
        # 算法公平性建议
        if evaluations.get("algorithm_fairness", {}).get("awareness_level") != "高度自觉":
            suggestions.append("加强算法公平性考虑，避免潜在的歧视问题")
        
        # 社会价值提升建议
        bonus_scores = {
            "social_impact": evaluations.get("social_impact", {}).get("score", 0),
            "environmental_friendliness": evaluations.get("environmental_friendliness", {}).get("score", 0),
            "charity_orientation": evaluations.get("charity_orientation", {}).get("score", 0),
            "long_term_vision": evaluations.get("long_term_vision", {}).get("score", 0),
        }
        
        # 选择得分最低的维度作为改进重点
        lowest_dim = min(bonus_scores, key=bonus_scores.get)
        if bonus_scores[lowest_dim] < 60:
            dim_map = {
                "social_impact": "社会影响深度",
                "environmental_friendliness": "环境可持续性",
                "charity_orientation": "公益普惠导向",
                "long_term_vision": "长期愿景与变革潜力",
            }
            suggestions.append(f"加强{dim_map.get(lowest_dim)}维度的建设，提升项目的社会价值")
        
        return suggestions[:3]
    
    def _generate_judge_focus_points(self, evaluations: Dict[str, Any], repo_info: RepoInfo) -> List[str]:
        """生成评委关注点"""
        points = []
        
        # 伦理安全关注点
        if evaluations.get("ethics_redline", {}).get("risk_level") != "安全":
            points.append(f"项目存在伦理风险，需要团队详细说明风险管控措施")
        
        # 社会价值关注点
        social_impact_score = evaluations.get("social_impact", {}).get("score", 0)
        if social_impact_score >= 70:
            points.append("项目社会影响显著，需要团队说明具体的实施路径和预期效果")
        
        # 环境友好关注点
        if evaluations.get("environmental_friendliness", {}).get("green_level") == "高":
            points.append("项目环境友好性强，需要团队提供具体的环境效益评估")
        
        # 公益普惠关注点
        if evaluations.get("charity_orientation", {}).get("charity_level") == "高":
            points.append("项目公益导向明显，需要团队说明可持续运营模式")
        
        # 长期愿景关注点
        if evaluations.get("long_term_vision", {}).get("vision_level") == "高":
            points.append("项目愿景宏大，需要团队说明从当前到愿景的具体实施计划")
        
        # 通用关注点
        points.append("请团队说明项目的核心社会价值主张和与其他方案的差异化优势")
        
        return points[:5]
    
    def analyze(self, repo_url: str, weights: Dict[str, float] = None,
               progress_callback=None) -> SocialValueReport:
        """
        分析仓库社会价值
        """
        start_time = time.time()
        
        weights = weights or DEFAULT_WEIGHTS.copy()
        weights = self._normalize_weights(weights)
        
        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
        
        # Step 1: 获取仓库信息
        update_progress(0.1, "正在获取GitHub仓库信息...")
        repo_info = self.github_fetcher.fetch(repo_url)
        
        # Step 2: 基础项评估
        update_progress(0.2, "正在评估伦理安全合规性...")
        ethics_eval = self._evaluate_ethics_redline(repo_info)
        privacy_eval = self._evaluate_privacy_protection(repo_info)
        fairness_eval = self._evaluate_algorithm_fairness(repo_info)
        
        # Step 3: 加分项评估
        update_progress(0.4, "正在评估社会影响深度...")
        social_impact_eval = self._evaluate_social_impact(repo_info)
        
        update_progress(0.55, "正在评估环境可持续性...")
        environmental_eval = self._evaluate_environmental_friendliness(repo_info)
        
        update_progress(0.7, "正在评估公益普惠导向...")
        charity_eval = self._evaluate_charity_orientation(repo_info)
        
        update_progress(0.85, "正在评估长期愿景...")
        vision_eval = self._evaluate_long_term_vision(repo_info)
        
        # 汇总评估结果
        evaluations = {
            "ethics_redline": ethics_eval,
            "privacy_protection": privacy_eval,
            "algorithm_fairness": fairness_eval,
            "social_impact": social_impact_eval,
            "environmental_friendliness": environmental_eval,
            "charity_orientation": charity_eval,
            "long_term_vision": vision_eval,
        }
        
        # Step 4: 计算7个子维度得分
        update_progress(0.9, "正在生成评估报告...")
        
        dimension_scores = [
            # 基础项（30%）
            DimensionScore(
                name="ethics_redline",
                name_cn="伦理红线检查",
                score=ethics_eval["score"],
                weight=weights.get("ethics_redline", 10),
                weighted_score=ethics_eval["score"] * weights.get("ethics_redline", 10) / 100,
                details=ethics_eval["analysis"],
                category="basic",
            ),
            DimensionScore(
                name="privacy_protection",
                name_cn="隐私与数据保护",
                score=privacy_eval["score"],
                weight=weights.get("privacy_protection", 10),
                weighted_score=privacy_eval["score"] * weights.get("privacy_protection", 10) / 100,
                details=privacy_eval["analysis"],
                category="basic",
            ),
            DimensionScore(
                name="algorithm_fairness",
                name_cn="算法公平性意识",
                score=fairness_eval["score"],
                weight=weights.get("algorithm_fairness", 10),
                weighted_score=fairness_eval["score"] * weights.get("algorithm_fairness", 10) / 100,
                details=fairness_eval["analysis"],
                category="basic",
            ),
            # 加分项（70%）
            DimensionScore(
                name="social_impact",
                name_cn="社会影响深度",
                score=social_impact_eval["score"],
                weight=weights.get("social_impact", 25),
                weighted_score=social_impact_eval["score"] * weights.get("social_impact", 25) / 100,
                details=social_impact_eval["analysis"],
                category="bonus",
            ),
            DimensionScore(
                name="environmental_friendliness",
                name_cn="环境可持续性",
                score=environmental_eval["score"],
                weight=weights.get("environmental_friendliness", 15),
                weighted_score=environmental_eval["score"] * weights.get("environmental_friendliness", 15) / 100,
                details=environmental_eval["analysis"],
                category="bonus",
            ),
            DimensionScore(
                name="charity_orientation",
                name_cn="公益普惠导向",
                score=charity_eval["score"],
                weight=weights.get("charity_orientation", 15),
                weighted_score=charity_eval["score"] * weights.get("charity_orientation", 15) / 100,
                details=charity_eval["analysis"],
                category="bonus",
            ),
            DimensionScore(
                name="long_term_vision",
                name_cn="长期愿景与变革潜力",
                score=vision_eval["score"],
                weight=weights.get("long_term_vision", 15),
                weighted_score=vision_eval["score"] * weights.get("long_term_vision", 15) / 100,
                details=vision_eval["analysis"],
                category="bonus",
            ),
        ]
        
        # 计算总分和板块分
        total_score = sum(d.weighted_score for d in dimension_scores)
        basic_items_score = sum(d.weighted_score for d in dimension_scores if d.category == "basic")
        bonus_items_score = sum(d.weighted_score for d in dimension_scores if d.category == "bonus")
        
        level, stars = self._get_level(total_score)
        
        # 详细维度分析
        dimension_analyses = {}
        for dim in dimension_scores:
            dimension_analyses[dim.name] = dim.details
        
        # 生成核心价值描述
        core_value = self._generate_core_value_summary(repo_info, evaluations)
        
        # 生成社会价值类型
        core_social_value_types = self._generate_social_value_types(evaluations)
        
        # 生成社会价值亮点
        social_value_highlights = self._generate_social_value_highlights(evaluations)
        
        # 生成改进建议
        improvement_suggestions = self._generate_improvement_suggestions(evaluations)
        
        # 生成评委关注点
        judge_focus_points = self._generate_judge_focus_points(evaluations, repo_info)
        
        # 评估置信度
        confidence_level = "中"
        if repo_info.description and len(repo_info.readme_content) > 500:
            confidence_level = "高"
            information_sufficiency = "高"
        elif not repo_info.description and len(repo_info.readme_content) < 200:
            confidence_level = "低"
            information_sufficiency = "低"
        else:
            information_sufficiency = "中"
        
        analysis_time = time.time() - start_time
        update_progress(1.0, "评估完成!")
        
        return SocialValueReport(
            repo_name=repo_info.name,
            repo_url=repo_url,
            total_score=total_score,
            level=level,
            level_stars=stars,
            core_value_summary=core_value,
            social_value_type=", ".join(core_social_value_types),
            basic_items_score=basic_items_score,
            bonus_items_score=bonus_items_score,
            dimensions=dimension_scores,
            stars=repo_info.stars,
            language=repo_info.language,
            description=repo_info.description,
            analysis_time=analysis_time,
            dimension_analyses=dimension_analyses,
            social_value_highlights=social_value_highlights,
            improvement_suggestions=improvement_suggestions,
            judge_focus_points=judge_focus_points,
            confidence_level=confidence_level,
            information_sufficiency=information_sufficiency,
            core_social_value_types=core_social_value_types,
        )
    
    def generate_markdown_report(self, report: SocialValueReport, use_llm: bool = None) -> str:
        """生成社会价值评估Markdown报告
        
        Args:
            report: 评估报告对象
            use_llm: 是否使用LLM优化报告，None表示使用默认设置
            
        Returns:
            Markdown格式的报告
        """
        # 是否使用LLM优化
        should_use_llm = use_llm if use_llm is not None else self.use_deepseek
        
        # 尝试使用DeepSeek模型优化报告
        if should_use_llm and self.report_optimizer:
            try:
                report_data = self._report_to_dict(report)
                
                # 准备提示词参数
                dim_table = "| 维度 | 得分 | 权重 | 加权得分 | 评价摘要 |\n|------|------|------|----------|----------|\n"
                for dim in report.dimensions:
                    dim_table += f"| {dim.name_cn} | {dim.score:.1f} | {dim.weight:.0f}% | {dim.weighted_score:.1f} | {dim.details[:50]}{'...' if len(dim.details) > 50 else ''} |\n"
                
                # 构建报告内容
                report_content = f"""
# 社会价值深度评估报告

## 项目基本信息
- 项目名称：{report.repo_name}
- 评估时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
- 核心社会价值类型：{', '.join(report.core_social_value_types)}

## 第一部分：基础项评估 - 伦理安全合规性

### 伦理红线检查
- **评估结论**：{self._get_ethics_conclusion(report.dimension_analyses.get('ethics_redline', ''))}
- **详细分析**：{report.dimension_analyses.get('ethics_redline', '评估数据不足')}
- **特别提醒**：{self._get_ethics_alert(report.dimension_analyses.get('ethics_redline', ''))}

### 隐私与数据保护
- **基本符合度**：{self._get_privacy_compliance(report.dimension_analyses.get('privacy_protection', ''))}
- **主要观察**：{report.dimension_analyses.get('privacy_protection', '评估数据不足')}

### 算法公平性意识
- **意识水平**：{self._get_fairness_awareness(report.dimension_analyses.get('algorithm_fairness', ''))}
- **具体表现**：{report.dimension_analyses.get('algorithm_fairness', '评估数据不足')}

## 第二部分：核心社会价值亮点深度分析

### 社会价值亮点
{chr(10).join([f"- {highlight}" for highlight in report.social_value_highlights])}

## 第三部分：其他维度简要评估

### 环境可持续性
- **简要评价**：{report.dimension_analyses.get('environmental_friendliness', '评估数据不足')}
- **是否值得深入**：{self._is_worth深入(report.dimension_analyses.get('environmental_friendliness', ''))}

### 公益普惠导向
- **简要评价**：{report.dimension_analyses.get('charity_orientation', '评估数据不足')}
- **是否值得深入**：{self._is_worth深入(report.dimension_analyses.get('charity_orientation', ''))}

### 长期愿景与变革潜力
- **简要评价**：{report.dimension_analyses.get('long_term_vision', '评估数据不足')}
- **是否值得深入**：{self._is_worth深入(report.dimension_analyses.get('long_term_vision', ''))}

## 第四部分：综合评估与建议

### 总体社会价值评价
- **核心优势**：{', '.join(report.social_value_highlights[:2])}
- **独特价值**：{report.core_value_summary}
- **实现可能性**：{self._get_implementation_possibility(total_score=report.total_score)}

### 给参赛者的社会价值优化建议
{chr(10).join([f"1. **{suggestion}**" for suggestion in report.improvement_suggestions])}

### 给评委的特别关注点
{chr(10).join([f"1. **{point}**" for point in report.judge_focus_points[:2]])}

## 第五部分：评估置信度
- **信息充分性**：{report.information_sufficiency}
- **评估确定性**：{report.confidence_level}
- **需要澄清的问题**：{self._get_clarification_questions(report.judge_focus_points)}

---
*报告生成时间: {report.analysis_time:.1f}秒 | AI黑客松社会价值评估系统 v1.0*
                """
                
                return report_content
            except Exception as e:
                print(f"LLM optimization failed, fallback to template: {e}")
        
        # 使用模板生成报告（fallback）
        return self._generate_template_report(report)
    
    def _get_ethics_conclusion(self, analysis: str) -> str:
        """获取伦理红线检查结论"""
        if "危险" in analysis:
            return "危险"
        elif "需关注" in analysis:
            return "需关注"
        else:
            return "安全"
    
    def _get_ethics_alert(self, analysis: str) -> str:
        """获取伦理红线特别提醒"""
        if "危险" in analysis:
            return "⚠️ 发现严重伦理风险，建议评委重点关注"
        elif "需关注" in analysis:
            return "⚠️ 存在潜在伦理风险，建议进一步评估"
        else:
            return "未发现明显伦理风险"
    
    def _get_privacy_compliance(self, analysis: str) -> str:
        """获取隐私保护符合度"""
        if "符合" in analysis:
            return "符合"
        elif "基本符合" in analysis:
            return "基本符合"
        else:
            return "不符合"
    
    def _get_fairness_awareness(self, analysis: str) -> str:
        """获取算法公平性意识水平"""
        if "高度自觉" in analysis:
            return "高度自觉"
        elif "基本意识" in analysis:
            return "基本意识"
        else:
            return "缺乏考虑"
    
    def _is_worth深入(self, analysis: str) -> str:
        """判断是否值得深入评估"""
        if "高" in analysis or "强" in analysis:
            return "是，表现突出"
        else:
            return "否，表现一般"
    
    def _get_implementation_possibility(self, total_score: float) -> str:
        """获取实现可能性评估"""
        if total_score >= 80:
            return "高"
        elif total_score >= 60:
            return "中"
        else:
            return "低"
    
    def _get_clarification_questions(self, focus_points: List[str]) -> str:
        """获取需要澄清的问题"""
        if focus_points:
            return focus_points[0]
        else:
            return "无"
    
    def _generate_template_report(self, report: SocialValueReport) -> str:
        """生成模板报告"""
        import time
        
        report_content = f"""
# 社会价值深度评估报告

## 项目基本信息
- 项目名称：{report.repo_name}
- 评估时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
- 核心社会价值类型：{', '.join(report.core_social_value_types)}

## 第一部分：基础项评估 - 伦理安全合规性

### 伦理红线检查
- **评估结论**：安全
- **详细分析**：{report.dimension_analyses.get('ethics_redline', '评估数据不足')}
- **特别提醒**：未发现明显伦理风险

### 隐私与数据保护
- **基本符合度**：基本符合
- **主要观察**：{report.dimension_analyses.get('privacy_protection', '评估数据不足')}

### 算法公平性意识
- **意识水平**：基本意识
- **具体表现**：{report.dimension_analyses.get('algorithm_fairness', '评估数据不足')}

## 第二部分：核心社会价值亮点深度分析

### 社会价值亮点
{chr(10).join([f"- {highlight}" for highlight in report.social_value_highlights])}

## 第三部分：其他维度简要评估

### 环境可持续性
- **简要评价**：{report.dimension_analyses.get('environmental_friendliness', '评估数据不足')}
- **是否值得深入**：否，表现一般

### 公益普惠导向
- **简要评价**：{report.dimension_analyses.get('charity_orientation', '评估数据不足')}
- **是否值得深入**：否，表现一般

### 长期愿景与变革潜力
- **简要评价**：{report.dimension_analyses.get('long_term_vision', '评估数据不足')}
- **是否值得深入**：否，表现一般

## 第四部分：综合评估与建议

### 总体社会价值评价
- **核心优势**：{', '.join(report.social_value_highlights[:2])}
- **独特价值**：{report.core_value_summary}
- **实现可能性**：中

### 给参赛者的社会价值优化建议
{chr(10).join([f"1. **{suggestion}**" for suggestion in report.improvement_suggestions])}

### 给评委的特别关注点
{chr(10).join([f"1. **{point}**" for point in report.judge_focus_points[:2]])}

## 第五部分：评估置信度
- **信息充分性**：{report.information_sufficiency}
- **评估确定性**：{report.confidence_level}
- **需要澄清的问题**：{report.judge_focus_points[0] if report.judge_focus_points else '无'}

---
*报告生成时间: {report.analysis_time:.1f}秒 | AI黑客松社会价值评估系统 v1.0*
        """
        
        return report_content
    
    def _report_to_dict(self, report: SocialValueReport) -> dict:
        """将报告对象转换为字典"""
        return {
            "repo_name": report.repo_name,
            "repo_url": report.repo_url,
            "description": report.description,
            "total_score": report.total_score,
            "level": report.level,
            "level_stars": report.level_stars,
            "core_value_summary": report.core_value_summary,
            "core_social_value_types": report.core_social_value_types,
            "basic_items_score": report.basic_items_score,
            "bonus_items_score": report.bonus_items_score,
            "dimension_analyses": report.dimension_analyses,
            "social_value_highlights": report.social_value_highlights,
            "improvement_suggestions": report.improvement_suggestions,
            "judge_focus_points": report.judge_focus_points,
            "confidence_level": report.confidence_level,
            "information_sufficiency": report.information_sufficiency,
        }
