"""创新性评分引擎（人性化版本 v3.0）

全新评估框架：
- 技术创新力（40%）：技术选型与实现、系统架构与设计、工程化与可持续性
- 场景创新力（60%）：问题定义与价值、场景创新性（重点）、市场与生态契合度

特点：
- 更注重应用场景的创新价值
- 人性化的报告语言
- 为评委提供实用参考
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import time
import re

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import DEFAULT_WEIGHTS, INNOVATION_LEVELS

from .github_fetcher import GitHubFetcher, RepoInfo
from .tech_stack_analyzer import TechStackAnalyzer, TechStackResult
from .architecture_analyzer import ArchitectureAnalyzer, ArchitectureResult
from .code_analyzer import CodeAnalyzer, CodeAnalysisResult
from .engineering_analyzer import EngineeringAnalyzer, EngineeringResult
from .solution_analyzer import SolutionAnalyzer, SolutionResult
from .report_optimizer import ReportOptimizer
from .report_quality import ReportQualityEvaluator
from .prompt_engineering import get_prompt_library, generate_prompt


@dataclass
class DimensionScore:
    """单个维度得分"""
    name: str
    name_cn: str
    score: float  # 原始得分 0-100
    weight: float  # 权重 0-100
    weighted_score: float  # 加权得分
    details: str  # 详细说明
    category: str = ""  # 所属大类：tech 或 scenario


@dataclass
class InnovationReport:
    """创新性评估报告（人性化版本）"""
    repo_name: str
    repo_url: str
    
    # 总分和等级
    total_score: float
    level: str
    level_stars: str
    
    # 一句话核心定位
    core_value_summary: str = ""  # 项目是什么及核心价值
    innovation_type: str = ""  # 定性评价语
    
    # 两大板块得分
    tech_innovation_score: float = 0.0  # 技术创新力总分（满分40）
    scenario_innovation_score: float = 0.0  # 场景创新力总分（满分60）
    
    # 6个子维度得分
    dimensions: List[DimensionScore] = field(default_factory=list)
    
    # 仓库元信息
    stars: int = 0
    language: str = ""
    description: str = ""
    
    # 分析时间
    analysis_time: float = 0.0
    
    # 雷达图数据（6维度，0-100）
    radar_scores: Dict[str, float] = field(default_factory=dict)
    radar_analysis: str = ""  # 雷达图解读（优势和短板）
    
    # 详细维度分析
    dimension_analyses: Dict[str, str] = field(default_factory=dict)
    
    # 具体改进建议（3类）
    tech_suggestions: List[str] = field(default_factory=list)  # 技术加固
    scenario_suggestions: List[str] = field(default_factory=list)  # 场景深化
    product_suggestions: List[str] = field(default_factory=list)  # 产品化推进
    
    # 评委关注点
    judge_focus_points: List[str] = field(default_factory=list)
    
    # 扩展分析数据
    tech_details: Dict[str, Any] = field(default_factory=dict)
    code_details: Dict[str, Any] = field(default_factory=dict)
    arch_details: Dict[str, Any] = field(default_factory=dict)
    eng_details: Dict[str, Any] = field(default_factory=dict)
    solution_details: Dict[str, Any] = field(default_factory=dict)
    
    # 研究辅助数据
    research_links: Dict[str, str] = field(default_factory=dict)
    community_health: Dict[str, Any] = field(default_factory=dict)


class InnovationScorer:
    """创新性评分引擎（人性化版本）
    
    新版6维度框架：
    - 技术创新力（40%）
      - 技术选型与实现 (13%)
      - 系统架构与设计 (13%)
      - 工程化与可持续性 (14%)
    - 场景创新力（60%）
      - 问题定义与价值 (18%)
      - 场景创新性（重点）(24%)
      - 市场与生态契合度 (18%)
    """
    
    # 新版维度名称映射
    DIMENSION_NAMES = {
        "tech_implementation": "技术选型与实现",
        "architecture_design": "系统架构与设计",
        "engineering_sustainability": "工程化与可持续性",
        "problem_value": "问题定义与价值",
        "scenario_innovation": "场景创新性",
        "market_fit": "市场与生态契合度",
    }
    
    # 场景关键词（用于场景创新性评估）
    SCENARIO_KEYWORDS = {
        "healthcare": ["医疗", "健康", "患者", "诊断", "阿尔茨海默", "alzheimer", "medical", "health", "patient"],
        "education": ["教育", "学习", "教学", "学生", "培训", "education", "learning", "student", "teacher"],
        "elderly_care": ["老年", "养老", "陪伴", "elderly", "senior", "aging", "care"],
        "accessibility": ["无障碍", "残障", "辅助", "accessibility", "disability", "assistive"],
        "mental_health": ["心理", "情绪", "心灵", "mental", "emotion", "therapy", "counseling"],
        "environment": ["环保", "可持续", "绿色", "environment", "sustainable", "green", "climate"],
        "social_good": ["公益", "慈善", "社会", "social", "charity", "nonprofit", "community"],
        "creative": ["创作", "艺术", "音乐", "creative", "art", "music", "design"],
        "productivity": ["效率", "自动化", "工作流", "productivity", "automation", "workflow"],
        "developer_tools": ["开发者", "工具", "SDK", "API", "developer", "tools", "framework"],
    }
    
    def __init__(self, github_token: str = None, use_modelscope: bool = True, use_deepseek: bool = True):
        """初始化评分引擎
        
        Args:
            github_token: GitHub API Token
            use_modelscope: 是否使用魔搭API进行相似度计算
            use_deepseek: 是否使用DeepSeek模型优化报告
        """
        self.github_fetcher = GitHubFetcher(token=github_token)
        self.tech_analyzer = TechStackAnalyzer()
        self.arch_analyzer = ArchitectureAnalyzer()
        self.code_analyzer = CodeAnalyzer()
        self.eng_analyzer = EngineeringAnalyzer()
        self.solution_analyzer = SolutionAnalyzer()
        
        self.similarity_calculator = None
        if use_modelscope:
            try:
                from models.similarity import SimilarityCalculator
                self.similarity_calculator = SimilarityCalculator(use_modelscope=True)
            except:
                pass
        
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
        for (low, high), (level, stars) in INNOVATION_LEVELS.items():
            if low <= score <= high:
                return level, stars
        return "常规实现", "⭐"
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """归一化权重"""
        total = sum(weights.values())
        if total == 0:
            return DEFAULT_WEIGHTS.copy()
        return {k: v * 100 / total for k, v in weights.items()}
    
    def _detect_scenario_keywords(self, text: str) -> Dict[str, List[str]]:
        """检测场景关键词"""
        text_lower = text.lower()
        detected = {}
        for category, keywords in self.SCENARIO_KEYWORDS.items():
            found = [kw for kw in keywords if kw in text_lower]
            if found:
                detected[category] = found
        return detected
    
    def _evaluate_scenario_innovation(self, repo_info: RepoInfo, solution_result: SolutionResult) -> Dict[str, Any]:
        """
        评估场景创新性（核心评估维度）
        
        场景创新性考察：
        1. 应用场景是否新颖或有深度
        2. 是否服务特定人群或独特需求
        3. 解决方案在该场景下是否巧妙
        """
        full_text = f"{repo_info.description} {repo_info.readme_content}"
        detected_scenarios = self._detect_scenario_keywords(full_text)
        
        score = 40  # 基础分
        analysis_parts = []
        
        # 1. 场景识别与新颖性
        if detected_scenarios:
            scenario_names = {
                "healthcare": "医疗健康",
                "education": "教育培训", 
                "elderly_care": "银发经济/养老关怀",
                "accessibility": "无障碍/辅助技术",
                "mental_health": "心理健康",
                "environment": "环保可持续",
                "social_good": "社会公益",
                "creative": "创意创作",
                "productivity": "效率工具",
                "developer_tools": "开发者工具",
            }
            
            primary_scenarios = list(detected_scenarios.keys())[:2]
            scenario_labels = [scenario_names.get(s, s) for s in primary_scenarios]
            
            # 特定高价值场景加分
            high_value_scenarios = ["healthcare", "elderly_care", "accessibility", "mental_health", "social_good"]
            if any(s in detected_scenarios for s in high_value_scenarios):
                score += 25
                analysis_parts.append(f"项目聚焦于**{'/'.join(scenario_labels)}**领域，这是具有深远社会价值的应用方向")
            else:
                score += 15
                analysis_parts.append(f"项目定位于**{'/'.join(scenario_labels)}**领域")
        else:
            analysis_parts.append("项目的应用场景定位不够明确，建议在文档中清晰阐述目标用户和使用场景")
        
        # 2. 特定人群服务（如阿尔茨海默症患者、残障人士等）
        specific_groups = []
        if "alzheimer" in full_text.lower() or "阿尔茨海默" in full_text:
            specific_groups.append("阿尔茨海默症患者")
            score += 10
        if "elderly" in full_text.lower() or "老年" in full_text:
            specific_groups.append("老年群体")
            score += 5
        if "disabled" in full_text.lower() or "残障" in full_text or "无障碍" in full_text:
            specific_groups.append("残障人士")
            score += 10
        if "child" in full_text.lower() or "儿童" in full_text:
            specific_groups.append("儿童群体")
            score += 5
        
        if specific_groups:
            analysis_parts.append(f"明确服务于{'/'.join(specific_groups)}，展现了对特定人群需求的深刻理解")
        
        # 3. 跨领域融合
        if solution_result.cross_domain and len(detected_scenarios) >= 2:
            score += 10
            analysis_parts.append("实现了跨领域技术融合，体现创新思维")
        
        # 4. 问题解决的巧妙性（基于README质量）
        if solution_result.problem_clarity > 0.7:
            score += 5
            analysis_parts.append("问题定义清晰，解决方案针对性强")
        
        score = min(100, score)
        
        return {
            "score": score,
            "detected_scenarios": detected_scenarios,
            "specific_groups": specific_groups,
            "analysis": "；".join(analysis_parts) if analysis_parts else "场景创新性有待提升",
        }
    
    def _evaluate_market_fit(self, repo_info: RepoInfo, tech_result: TechStackResult, 
                            solution_result: SolutionResult) -> Dict[str, Any]:
        """
        评估市场与生态契合度
        
        考察：
        1. 与现有方案的差异化
        2. 是否顺应技术趋势
        3. 是否易于融入其他产品/生态
        """
        score = 40  # 基础分
        analysis_parts = []
        
        # 1. 技术趋势契合度
        if tech_result.cutting_edge_packages:
            score += 20
            analysis_parts.append(f"采用{', '.join(tech_result.cutting_edge_packages[:2])}等前沿技术，顺应AI应用发展趋势")
        elif tech_result.modern_packages:
            score += 10
            analysis_parts.append("技术选型主流稳定，生态兼容性好")
        
        # 2. 市场验证（Star数作为参考）
        if repo_info.stars > 1000:
            score += 15
            analysis_parts.append(f"已获{repo_info.stars:,}个Star，得到社区认可")
        elif repo_info.stars > 100:
            score += 8
            analysis_parts.append("有一定社区关注度")
        
        # 3. 生态集成能力
        deps = tech_result.packages
        integration_indicators = ["api", "sdk", "plugin", "extension", "integration", "webhook"]
        full_text = f"{repo_info.description} {repo_info.readme_content}".lower()
        
        if any(ind in full_text for ind in integration_indicators):
            score += 10
            analysis_parts.append("具备良好的集成能力，易于融入现有工作流")
        
        # 4. 开源生态（License）
        license_name = getattr(repo_info, 'license_name', '')
        if license_name and 'mit' in license_name.lower() or 'apache' in license_name.lower():
            score += 5
            analysis_parts.append("采用开放许可协议，便于商业采用")
        
        score = min(100, score)
        
        return {
            "score": score,
            "analysis": "；".join(analysis_parts) if analysis_parts else "市场契合度有提升空间",
        }
    
    def _generate_core_value_summary(self, repo_info: RepoInfo, scenario_eval: Dict) -> str:
        """生成项目核心价值一句话描述"""
        name = repo_info.name
        desc = repo_info.description or ""
        
        # 检测场景
        scenarios = scenario_eval.get("detected_scenarios", {})
        specific_groups = scenario_eval.get("specific_groups", [])
        
        scenario_names = {
            "healthcare": "医疗健康",
            "education": "教育培训",
            "elderly_care": "养老关怀",
            "accessibility": "无障碍辅助",
            "mental_health": "心理健康",
            "environment": "环保",
            "social_good": "社会公益",
            "creative": "创意创作",
            "productivity": "效率提升",
            "developer_tools": "开发者工具",
        }
        
        if specific_groups:
            target = specific_groups[0]
            return f"**{name}** 是一个面向{target}的AI应用，{desc[:50]}{'...' if len(desc) > 50 else ''}"
        elif scenarios:
            primary = list(scenarios.keys())[0]
            scenario_label = scenario_names.get(primary, primary)
            return f"**{name}** 是一个{scenario_label}领域的AI应用，{desc[:50]}{'...' if len(desc) > 50 else ''}"
        else:
            return f"**{name}** 是一个AI应用项目，{desc[:60]}{'...' if len(desc) > 60 else ''}"
    
    def _generate_innovation_type(self, total_score: float, tech_score: float, 
                                  scenario_score: float, scenario_eval: Dict) -> str:
        """生成创新类型定性评价"""
        # 场景得分占比高
        if scenario_score > tech_score * 1.2:
            if scenario_eval.get("specific_groups"):
                return "聚焦特定人群的社会价值型创新"
            else:
                return "场景驱动的实用型创新"
        # 技术得分占比高
        elif tech_score > scenario_score * 0.8:
            return "技术领先的工程型创新"
        # 均衡
        else:
            if total_score >= 75:
                return "技术与场景兼备的综合型创新"
            elif total_score >= 60:
                return "中等创新力的应用型项目"
            else:
                return "渐进改进型项目"
    
    def _generate_radar_analysis(self, radar_scores: Dict[str, float]) -> str:
        """生成雷达图解读（优势和短板）"""
        sorted_dims = sorted(radar_scores.items(), key=lambda x: x[1], reverse=True)
        
        dim_names = {
            "tech_implementation": "技术选型与实现",
            "architecture_design": "系统架构与设计",
            "engineering_sustainability": "工程化与可持续性",
            "problem_value": "问题定义与价值",
            "scenario_innovation": "场景创新性",
            "market_fit": "市场与生态契合度",
        }
        
        strengths = [(dim_names[k], v) for k, v in sorted_dims[:2] if v >= 60]
        weaknesses = [(dim_names[k], v) for k, v in sorted_dims[-2:] if v < 60]
        
        parts = []
        if strengths:
            strength_str = "、".join([f"{name}({score:.0f}分)" for name, score in strengths])
            parts.append(f"**优势维度**：{strength_str}")
        
        if weaknesses:
            weakness_str = "、".join([f"{name}({score:.0f}分)" for name, score in weaknesses])
            parts.append(f"**待提升维度**：{weakness_str}")
        
        return "\n\n".join(parts) if parts else "各维度表现较为均衡"
    
    def _generate_dimension_analysis(self, dim_name: str, score: float, 
                                     tech_result, arch_result, code_result, 
                                     eng_result, solution_result, repo_info,
                                     scenario_eval, market_eval) -> str:
        """生成单个维度的详细分析"""
        
        if dim_name == "tech_implementation":
            if tech_result.cutting_edge_packages:
                return f"项目采用了{', '.join(tech_result.cutting_edge_packages[:3])}等前沿技术，技术选型具有前瞻性。代码质量{'良好' if code_result.avg_complexity < 8 else '复杂度较高'}，实现较为{'规范' if code_result.total_classes > 0 else '直接'}。"
            elif tech_result.modern_packages:
                return f"使用{', '.join(tech_result.modern_packages[:3])}等主流技术栈，选型成熟稳定。建议关注更前沿的技术方案以提升技术创新性。"
            else:
                return "技术选型较为基础，主要使用标准库和常规工具。建议引入更现代的框架和工具提升技术层次。"
        
        elif dim_name == "architecture_design":
            arch_type = getattr(arch_result, 'architecture_type', '')
            coupling = getattr(arch_result, 'coupling_assessment', '')
            if arch_result.detected_patterns:
                return f"项目采用{arch_type or '模块化'}架构，识别到{', '.join(arch_result.detected_patterns)}等设计模式。{coupling}，代码组织{'清晰' if arch_result.module_count >= 5 else '简洁'}，{'易于未来扩展' if not arch_result.is_standard_template else '但结构较为模板化'}。"
            else:
                return f"项目结构较为{'标准化' if arch_result.is_standard_template else '简单'}，目录层级{arch_result.directory_depth}层，模块数{arch_result.module_count}个。建议采用更清晰的模块化设计提升可维护性。"
        
        elif dim_name == "engineering_sustainability":
            features = []
            if eng_result.has_ci_cd:
                features.append("CI/CD自动化")
            if eng_result.has_docker:
                features.append("容器化部署")
            if eng_result.has_tests:
                features.append(f"测试覆盖({eng_result.test_file_count}个测试文件)")
            
            if features:
                return f"工程化配置较为完善，具备{' + '.join(features)}，可持续维护能力{'强' if len(features) >= 2 else '中等'}。"
            else:
                return "工程化配置有待加强，建议添加自动化测试、CI/CD流程和容器化部署方案，提升项目的可持续性。"
        
        elif dim_name == "problem_value":
            clarity = solution_result.problem_clarity
            if clarity > 0.7:
                return f"问题定义清晰（清晰度{clarity*100:.0f}%），目标用户和核心痛点描述明确。README文档结构完整，便于理解项目价值主张。"
            elif clarity > 0.4:
                return f"问题定义基本清晰（清晰度{clarity*100:.0f}%），但可进一步细化用户画像和价值主张。建议在文档中更明确阐述'为谁解决什么问题'。"
            else:
                return "问题定义不够清晰，建议完善README，明确阐述目标用户、核心痛点和解决方案的独特价值。"
        
        elif dim_name == "scenario_innovation":
            return scenario_eval.get("analysis", "场景创新性评估数据不足")
        
        elif dim_name == "market_fit":
            return market_eval.get("analysis", "市场契合度评估数据不足")
        
        return "分析数据不足"
    
    def _generate_suggestions(self, tech_result, arch_result, code_result, 
                             eng_result, solution_result, scenario_eval) -> Dict[str, List[Dict[str, str]]]:
        """生成三类改进建议（详细版）"""
        tech_suggestions = []
        scenario_suggestions = []
        product_suggestions = []
        
        # 技术加固建议
        if not tech_result.cutting_edge_packages:
            tech_suggestions.append({
                "title": "引入前沿AI框架",
                "description": "引入LangChain、AutoGen等前沿AI框架，提升技术创新性",
                "reason": "当前技术栈较为基础，缺乏前沿AI技术应用",
                "measures": "1. 集成LangChain框架实现复杂的AI工作流\n2. 引入AutoGen实现多智能体协作\n3. 探索RAG技术提升系统性能",
                "expected_effect": "显著提升技术创新性评分，增强系统功能复杂度",
                "priority": "高"
            })
        if code_result.avg_complexity < 2:
            tech_suggestions.append({
                "title": "增强核心算法实现",
                "description": "增加核心算法的自定义实现，减少对第三方库的简单封装",
                "reason": "代码复杂度低，创新性不足，主要依赖第三方库",
                "measures": "1. 实现自定义的AI模型或算法\n2. 优化现有算法的时间/空间复杂度\n3. 添加创新的技术组件",
                "expected_effect": "提升技术实现创新性，展现团队技术实力",
                "priority": "高"
            })
        if not arch_result.detected_patterns:
            tech_suggestions.append({
                "title": "优化系统架构设计",
                "description": "采用清晰的架构模式，提升代码可维护性和扩展性",
                "reason": "缺乏明确的架构模式，代码组织不够结构化",
                "measures": "1. 采用Clean Architecture架构\n2. 实现模块化设计\n3. 建立清晰的依赖关系",
                "expected_effect": "提升架构设计评分，增强系统可维护性",
                "priority": "中"
            })
        if not eng_result.has_tests:
            tech_suggestions.append({
                "title": "完善测试体系",
                "description": "添加单元测试和集成测试，确保代码质量和稳定性",
                "reason": "缺乏测试覆盖，代码质量和稳定性无法保障",
                "measures": "1. 编写单元测试覆盖核心功能\n2. 实现集成测试验证系统流程\n3. 配置测试覆盖率统计",
                "expected_effect": "提升工程化评分，增强代码稳定性",
                "priority": "中"
            })
        
        # 场景深化建议
        if not scenario_eval.get("specific_groups"):
            scenario_suggestions.append({
                "title": "明确目标用户群体",
                "description": "深入理解特定用户群体的真实需求和使用场景",
                "reason": "目标用户不明确，场景创新性缺乏针对性",
                "measures": "1. 进行用户调研和访谈\n2. 创建详细的用户画像\n3. 分析目标用户的具体痛点",
                "expected_effect": "显著提升场景创新性评分，增强项目的针对性",
                "priority": "高"
            })
        if solution_result.problem_clarity < 0.6:
            scenario_suggestions.append({
                "title": "完善问题定义",
                "description": "清晰阐述'为谁解决什么问题'以及'为何现有方案不足'",
                "reason": "问题定义不够清晰，价值主张不明确",
                "measures": "1. 编写详细的问题分析文档\n2. 对比现有解决方案的不足\n3. 明确项目的独特价值",
                "expected_effect": "提升问题定义与价值评分，使项目方向更清晰",
                "priority": "高"
            })
        if not scenario_eval.get("detected_scenarios"):
            scenario_suggestions.append({
                "title": "聚焦高价值应用场景",
                "description": "明确应用场景定位，考虑具有社会价值的领域",
                "reason": "应用场景不明确，缺乏社会价值体现",
                "measures": "1. 聚焦医疗健康、教育、养老等领域\n2. 深入挖掘特定场景的需求\n3. 设计针对性的解决方案",
                "expected_effect": "显著提升场景创新性评分，增加项目社会影响力",
                "priority": "高"
            })
        scenario_suggestions.append({
            "title": "建立用户反馈机制",
            "description": "收集真实用户反馈，持续迭代优化产品",
            "reason": "缺乏用户反馈渠道，产品迭代缺乏数据支持",
            "measures": "1. 建立用户反馈收集系统\n2. 定期分析用户反馈\n3. 基于反馈持续优化产品",
            "expected_effect": "提升产品用户体验，验证场景创新性",
            "priority": "中"
        })
        
        # 产品化推进建议
        if not eng_result.has_docker:
            product_suggestions.append({
                "title": "添加容器化支持",
                "description": "添加Docker配置，简化部署流程，便于快速演示",
                "reason": "缺乏容器化支持，部署复杂，不便于评委快速体验",
                "measures": "1. 创建Dockerfile和docker-compose配置\n2. 优化容器镜像大小\n3. 提供一键启动脚本",
                "expected_effect": "提升工程化评分，便于评委快速体验项目",
                "priority": "中"
            })
        if not eng_result.has_ci_cd:
            product_suggestions.append({
                "title": "配置CI/CD流程",
                "description": "实现自动化测试和部署，提升开发效率",
                "reason": "缺乏自动化流程，开发效率低，代码质量难保障",
                "measures": "1. 配置GitHub Actions或Jenkins\n2. 实现自动化测试\n3. 配置自动部署流程",
                "expected_effect": "提升工程化评分，保障代码质量",
                "priority": "中"
            })
        product_suggestions.append({
            "title": "创建在线演示",
            "description": "创建在线Demo或演示视频，让评委快速体验核心功能",
            "reason": "缺乏直观的产品展示，评委难以理解项目价值",
            "measures": "1. 部署在线Demo环境\n2. 制作简短的功能演示视频\n3. 提供详细的使用说明",
            "expected_effect": "提升评委对项目的理解，展示产品价值",
            "priority": "高"
        })
        product_suggestions.append({
            "title": "完善技术文档",
            "description": "编写详细的技术博客或设计文档，阐述技术实现细节和创新点",
            "reason": "技术文档不完善，难以展现项目的技术创新性",
            "measures": "1. 编写详细的技术架构文档\n2. 创作技术博客分享创新点\n3. 制作技术实现的可视化图表",
            "expected_effect": "提升评委对技术创新性的认知，展现团队专业能力",
            "priority": "中"
        })
        
        return {
            "tech": tech_suggestions[:3],
            "scenario": scenario_suggestions[:3],
            "product": product_suggestions[:3],
        }
    
    def _generate_judge_focus_points(self, total_score, tech_result, scenario_eval, 
                                     solution_result, repo_info) -> List[Dict[str, str]]:
        """生成评委关注点（详细版）"""
        points = []
        
        # 基于场景的问题
        if scenario_eval.get("specific_groups"):
            groups = scenario_eval["specific_groups"]
            points.append({
                "question": f"项目声称服务于{groups[0]}，请团队阐述如何深入理解该群体的真实需求？是否有用户调研或实际测试反馈？",
                "purpose": "评估团队对目标用户群体的理解深度和用户研究能力",
                "expected_answer": "希望团队能提供具体的用户调研方法、收集的反馈数据、以及如何根据用户需求进行产品设计的具体案例",
                "scoring_criteria": "优秀：有详细的用户调研计划和数据支持；良好：有基本的用户理解；一般：仅基于主观判断；差：缺乏用户理解"
            })
        
        # 基于技术的问题
        deps = tech_result.packages
        if any(d.lower() in ['openai', 'anthropic', 'claude'] for d in deps):
            points.append({
                "question": "项目依赖商业LLM API，在API封装之上做了哪些增值创新？如何应对API成本和服务稳定性问题？",
                "purpose": "评估团队的技术创新能力和商业化思考",
                "expected_answer": "希望团队能详细说明在API基础上的技术创新点，以及具体的成本控制和服务稳定性保障措施",
                "scoring_criteria": "优秀：有显著的技术创新和完善的成本控制方案；良好：有一定创新和基本控制措施；一般：仅简单封装；差：无创新且缺乏成本考虑"
            })
        
        # 基于复杂度的问题
        if total_score >= 70:
            points.append({
                "question": "请团队现场演示核心功能，并说明技术实现的关键创新点是什么？",
                "purpose": "验证项目的实际功能和技术创新性",
                "expected_answer": "希望团队能流畅演示核心功能，并清晰阐述技术实现中的创新点和技术挑战",
                "scoring_criteria": "优秀：功能完整且有显著技术创新；良好：功能基本完整有一定创新；一般：功能简单创新不足；差：功能不完整无创新"
            })
        
        # 通用问题 - 差异化竞争力
        points.append({
            "question": "与市场上同类产品相比，本项目的核心差异化竞争力是什么？",
            "purpose": "评估项目的市场定位和竞争优势",
            "expected_answer": "希望团队能清晰阐述与竞品的具体差异点，以及这些差异如何形成竞争优势",
            "scoring_criteria": "优秀：有明确的差异化优势和市场定位；良好：有一定差异化但不够突出；一般：差异化不明显；差：缺乏差异化认知"
        })
        
        # 基于社区反馈的问题
        if repo_info.stars > 500:
            points.append({
                "question": f"项目已获得{repo_info.stars}个Star，用户主要反馈了哪些问题？未来发展规划是什么？",
                "purpose": "评估项目的社区运营能力和长期发展规划",
                "expected_answer": "希望团队能分享用户反馈的具体问题，以及基于这些反馈的产品迭代计划和长期发展愿景",
                "scoring_criteria": "优秀：有详细的用户反馈分析和清晰的发展规划；良好：有基本的反馈收集和规划；一般：反馈收集不足；差：缺乏反馈意识和规划"
            })
        
        # 技术架构问题
        points.append({
            "question": "请详细说明项目的系统架构设计，以及这种设计如何支持产品的创新性和可扩展性？",
            "purpose": "评估项目的架构设计能力和技术远见",
            "expected_answer": "希望团队能清晰阐述系统架构的设计思路、关键组件、以及如何支持产品功能和未来扩展",
            "scoring_criteria": "优秀：架构设计清晰合理且有技术远见；良好：架构基本合理；一般：架构设计简单；差：架构混乱缺乏规划"
        })
        
        # 场景创新性问题
        points.append({
            "question": "项目的应用场景创新性体现在哪些方面？与传统解决方案相比有哪些显著优势？",
            "purpose": "评估项目的场景创新性和问题解决能力",
            "expected_answer": "希望团队能详细说明场景创新点，以及如何通过技术手段解决传统方案的不足",
            "scoring_criteria": "优秀：场景创新显著且有具体价值；良好：有一定场景创新；一般：场景创新不足；差：缺乏场景创新"
        })
        
        return points[:5]
    
    def analyze(self, repo_url: str, weights: Dict[str, float] = None,
               progress_callback=None) -> InnovationReport:
        """
        分析仓库创新性（人性化版本）
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
        
        # Step 2: 基础分析
        update_progress(0.2, "正在分析技术选型...")
        tech_result = self.tech_analyzer.analyze(
            requirements_content=repo_info.requirements_content,
            pyproject_content=repo_info.pyproject_content,
        )
        
        update_progress(0.3, "正在分析系统架构...")
        arch_result = self.arch_analyzer.analyze(
            directory_tree=repo_info.directory_tree,
            python_files=repo_info.python_files,
        )
        
        update_progress(0.4, "正在分析代码实现...")
        code_result = self.code_analyzer.analyze(
            code_files=repo_info.code_files,
        )
        
        update_progress(0.5, "正在分析工程化程度...")
        eng_result = self.eng_analyzer.analyze(
            directory_tree=repo_info.directory_tree,
            python_files=repo_info.python_files,
            readme_content=repo_info.readme_content,
        )
        
        update_progress(0.6, "正在分析问题定义...")
        solution_result = self.solution_analyzer.analyze(
            readme_content=repo_info.readme_content,
        )
        
        # Step 3: 场景创新性评估（核心）
        update_progress(0.7, "正在评估场景创新性...")
        scenario_eval = self._evaluate_scenario_innovation(repo_info, solution_result)
        
        # Step 4: 市场契合度评估
        update_progress(0.8, "正在评估市场契合度...")
        market_eval = self._evaluate_market_fit(repo_info, tech_result, solution_result)
        
        # Step 5: 计算6个子维度得分
        update_progress(0.9, "正在生成评估报告...")
        
        dimension_scores = [
            # 技术创新力（40%）
            DimensionScore(
                name="tech_implementation",
                name_cn="技术选型与实现",
                score=tech_result.score,
                weight=weights.get("tech_implementation", 13),
                weighted_score=tech_result.score * weights.get("tech_implementation", 13) / 100,
                details=tech_result.details,
                category="tech",
            ),
            DimensionScore(
                name="architecture_design",
                name_cn="系统架构与设计",
                score=arch_result.score,
                weight=weights.get("architecture_design", 13),
                weighted_score=arch_result.score * weights.get("architecture_design", 13) / 100,
                details=arch_result.details,
                category="tech",
            ),
            DimensionScore(
                name="engineering_sustainability",
                name_cn="工程化与可持续性",
                score=eng_result.score,
                weight=weights.get("engineering_sustainability", 14),
                weighted_score=eng_result.score * weights.get("engineering_sustainability", 14) / 100,
                details=eng_result.details,
                category="tech",
            ),
            # 场景创新力（60%）
            DimensionScore(
                name="problem_value",
                name_cn="问题定义与价值",
                score=solution_result.score,
                weight=weights.get("problem_value", 18),
                weighted_score=solution_result.score * weights.get("problem_value", 18) / 100,
                details=solution_result.details,
                category="scenario",
            ),
            DimensionScore(
                name="scenario_innovation",
                name_cn="场景创新性",
                score=scenario_eval["score"],
                weight=weights.get("scenario_innovation", 24),
                weighted_score=scenario_eval["score"] * weights.get("scenario_innovation", 24) / 100,
                details=scenario_eval["analysis"],
                category="scenario",
            ),
            DimensionScore(
                name="market_fit",
                name_cn="市场与生态契合度",
                score=market_eval["score"],
                weight=weights.get("market_fit", 18),
                weighted_score=market_eval["score"] * weights.get("market_fit", 18) / 100,
                details=market_eval["analysis"],
                category="scenario",
            ),
        ]
        
        # 计算总分和板块分
        total_score = sum(d.weighted_score for d in dimension_scores)
        tech_innovation_score = sum(d.weighted_score for d in dimension_scores if d.category == "tech")
        scenario_innovation_score = sum(d.weighted_score for d in dimension_scores if d.category == "scenario")
        
        level, stars = self._get_level(total_score)
        
        # 雷达图数据
        radar_scores = {d.name: d.score for d in dimension_scores}
        radar_analysis = self._generate_radar_analysis(radar_scores)
        
        # 详细维度分析
        dimension_analyses = {}
        for dim in dimension_scores:
            dimension_analyses[dim.name] = self._generate_dimension_analysis(
                dim.name, dim.score, tech_result, arch_result, code_result,
                eng_result, solution_result, repo_info, scenario_eval, market_eval
            )
        
        # 生成建议
        suggestions = self._generate_suggestions(
            tech_result, arch_result, code_result, eng_result, solution_result, scenario_eval
        )
        
        # 生成评委关注点
        judge_focus = self._generate_judge_focus_points(
            total_score, tech_result, scenario_eval, solution_result, repo_info
        )
        
        # 生成核心价值描述
        core_value = self._generate_core_value_summary(repo_info, scenario_eval)
        innovation_type = self._generate_innovation_type(
            total_score, tech_innovation_score, scenario_innovation_score, scenario_eval
        )
        
        analysis_time = time.time() - start_time
        update_progress(1.0, "评估完成!")
        
        return InnovationReport(
            repo_name=repo_info.name,
            repo_url=repo_url,
            total_score=total_score,
            level=level,
            level_stars=stars,
            core_value_summary=core_value,
            innovation_type=innovation_type,
            tech_innovation_score=tech_innovation_score,
            scenario_innovation_score=scenario_innovation_score,
            dimensions=dimension_scores,
            stars=repo_info.stars,
            language=repo_info.language,
            description=repo_info.description,
            analysis_time=analysis_time,
            radar_scores=radar_scores,
            radar_analysis=radar_analysis,
            dimension_analyses=dimension_analyses,
            tech_suggestions=suggestions["tech"],
            scenario_suggestions=suggestions["scenario"],
            product_suggestions=suggestions["product"],
            judge_focus_points=judge_focus,
            tech_details={
                "packages": tech_result.packages,
                "cutting_edge": tech_result.cutting_edge_packages,
                "modern": tech_result.modern_packages,
            },
            code_details={
                "total_functions": code_result.total_functions,
                "total_classes": code_result.total_classes,
                "avg_complexity": code_result.avg_complexity,
            },
            arch_details={
                "patterns": arch_result.detected_patterns,
                "depth": arch_result.directory_depth,
                "modules": arch_result.module_count,
            },
            eng_details={
                "has_ci_cd": eng_result.has_ci_cd,
                "has_docker": eng_result.has_docker,
                "has_tests": eng_result.has_tests,
            },
            solution_details={
                "problem_clarity": solution_result.problem_clarity,
                "cross_domain": solution_result.cross_domain,
                "domain_tags": solution_result.domain_tags,
            },
            research_links=getattr(repo_info, 'research_links', {}),
            community_health={
                "stars": repo_info.stars,
                "contributors": getattr(repo_info, 'contributors_count', 0),
                "issues": getattr(repo_info, 'open_issues_count', 0),
            },
        )
    
    def generate_markdown_report(self, report: InnovationReport, use_llm: bool = None) -> str:
        """生成人性化的Markdown报告
        
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
                
                analyses_text = ""
                for dim_name, analysis in report.dimension_analyses.items():
                    dim_cn = next((d.name_cn for d in report.dimensions if d.name == dim_name), dim_name)
                    analyses_text += f"### {dim_cn}\n{analysis}\n\n"
                
                tech_suggestions = ""
                for i, suggestion in enumerate(report.tech_suggestions, 1):
                    if isinstance(suggestion, dict):
                        tech_suggestions += f"- **{suggestion.get('title')}**：{suggestion.get('description')}（优先级：{suggestion.get('priority')}）\n"
                        tech_suggestions += f"  原因：{suggestion.get('reason', '')}\n"
                        tech_suggestions += f"  措施：{suggestion.get('measures', '')}\n"
                        tech_suggestions += f"  预期效果：{suggestion.get('expected_effect', '')}\n"
                    else:
                        tech_suggestions += f"- {suggestion}\n"
                
                scenario_suggestions = ""
                for i, suggestion in enumerate(report.scenario_suggestions, 1):
                    if isinstance(suggestion, dict):
                        scenario_suggestions += f"- **{suggestion.get('title')}**：{suggestion.get('description')}（优先级：{suggestion.get('priority')}）\n"
                        scenario_suggestions += f"  原因：{suggestion.get('reason', '')}\n"
                        scenario_suggestions += f"  措施：{suggestion.get('measures', '')}\n"
                        scenario_suggestions += f"  预期效果：{suggestion.get('expected_effect', '')}\n"
                    else:
                        scenario_suggestions += f"- {suggestion}\n"
                
                product_suggestions = ""
                for i, suggestion in enumerate(report.product_suggestions, 1):
                    if isinstance(suggestion, dict):
                        product_suggestions += f"- **{suggestion.get('title')}**：{suggestion.get('description')}（优先级：{suggestion.get('priority')}）\n"
                        product_suggestions += f"  原因：{suggestion.get('reason', '')}\n"
                        product_suggestions += f"  措施：{suggestion.get('measures', '')}\n"
                        product_suggestions += f"  预期效果：{suggestion.get('expected_effect', '')}\n"
                    else:
                        product_suggestions += f"- {suggestion}\n"
                
                judge_focus_points = ""
                for i, point in enumerate(report.judge_focus_points, 1):
                    if isinstance(point, dict):
                        judge_focus_points += f"- **{point.get('question')}**\n"
                        judge_focus_points += f"  追问目的：{point.get('purpose')}\n"
                        judge_focus_points += f"  期望回答：{point.get('expected_answer', '')}\n"
                        judge_focus_points += f"  评分参考：{point.get('scoring_criteria', '')}\n"
                    else:
                        judge_focus_points += f"- {point}\n"
                
                # 增加项目深度分析所需的数据
                project_depth_data = {
                    "tech_details": report.tech_details,
                    "code_details": report.code_details,
                    "arch_details": report.arch_details,
                    "eng_details": report.eng_details,
                    "solution_details": report.solution_details,
                    "research_links": report.research_links,
                    "community_health": report.community_health,
                    "core_value_summary": report.core_value_summary,
                    "innovation_type": report.innovation_type,
                }
                
                # 使用提示词工程库生成优化提示词
                prompt_data = {
                    "repo_name": report.repo_name,
                    "description": report.description,
                    "language": report.language,
                    "stars": report.stars,
                    "repo_url": report.repo_url,
                    "total_score": report.total_score,
                    "level": report.level,
                    "level_stars": report.level_stars,
                    "tech_innovation_score": report.tech_innovation_score,
                    "scenario_innovation_score": report.scenario_innovation_score,
                    "dim_table": dim_table,
                    "radar_analysis": report.radar_analysis,
                    "analyses_text": analyses_text,
                    "tech_suggestions": tech_suggestions,
                    "scenario_suggestions": scenario_suggestions,
                    "product_suggestions": product_suggestions,
                    "judge_focus_points": judge_focus_points,
                    "project_depth_data": project_depth_data
                }
                
                optimized = self.report_optimizer.optimize_report(report_data, prompt_data=prompt_data, timeout=300)
                if optimized:
                    # 评估报告质量
                    quality_result = self.quality_evaluator.evaluate(optimized)
                    quality_report = self.quality_evaluator.generate_quality_report(quality_result)
                    
                    # 添加页脚和质量评估
                    footer = f"\n\n---\n\n*报告生成时间: {report.analysis_time:.1f}秒 | SAGE AI创新性评估系统 v4.0（提示词工程优化版）*"
                    return optimized + footer + "\n\n" + quality_report
            except Exception as e:
                print(f"LLM optimization failed, fallback to template: {e}")
        
        # 使用模板生成报告（fallback）
        template_report = self._generate_template_report(report)
        
        # 评估报告质量
        quality_result = self.quality_evaluator.evaluate(template_report)
        quality_report = self.quality_evaluator.generate_quality_report(quality_result)
        
        return template_report + "\n\n" + quality_report
    
    def _report_to_dict(self, report: InnovationReport) -> dict:
        """将报告对象转换为字典"""
        return {
            "repo_name": report.repo_name,
            "repo_url": report.repo_url,
            "description": report.description,
            "language": report.language,
            "stars": report.stars,
            "total_score": report.total_score,
            "level": report.level,
            "level_stars": report.level_stars,
            "core_value_summary": report.core_value_summary,
            "innovation_type": report.innovation_type,
            "tech_innovation_score": report.tech_innovation_score,
            "scenario_innovation_score": report.scenario_innovation_score,
            "dimensions": [
                {
                    "name": d.name,
                    "name_cn": d.name_cn,
                    "score": d.score,
                    "weight": d.weight,
                    "details": d.details,
                    "category": d.category,
                }
                for d in report.dimensions
            ],
            "radar_analysis": report.radar_analysis,
            "dimension_analyses": report.dimension_analyses,
            "tech_suggestions": report.tech_suggestions,
            "scenario_suggestions": report.scenario_suggestions,
            "product_suggestions": report.product_suggestions,
            "judge_focus_points": report.judge_focus_points,
            "research_links": report.research_links,
        }
    
    def _generate_template_report(self, report: InnovationReport) -> str:
        """使用模板生成报告（无LLM优化）"""
        from datetime import datetime
        
        md = []
        
        # ============ 报告标题 ============
        md.append("# 📊 科创大赛 AI 评审 - 深度创新性评估报告")
        md.append("")
        md.append("---")
        md.append("")
        
        # ============ 项目本体画像 ============
        md.append("## 🚀 项目本体画像 (Project Identity)")
        md.append("")
        md.append(f"**项目名称**: [{report.repo_name}]({report.repo_url})")
        md.append(f"**核心愿景**: *{report.core_value_summary}*")
        md.append("")
        md.append("### 📝 项目概览")
        md.append(f"**编程语言**: {report.language or 'N/A'}")
        md.append(f"**社区热度**: {report.stars:,} Stars")
        md.append(f"**项目描述**: {report.description or 'N/A'}")
        md.append("")
        
        # ============ 创新性总评 ============
        md.append("## 🏆 创新性总评")
        md.append("")
        md.append(f"### 总体评分：{report.total_score:.1f}/100 {report.level_stars}")
        md.append("")
        md.append(f"**创新等级**：{report.level}")
        md.append(f"**定性评价**：{report.innovation_type}")
        md.append("")
        
        # 两大板块得分
        md.append("| 板块 | 得分 | 满分 | 占比 |")
        md.append("|------|------|------|------|")
        md.append(f"| 技术创新力 | {report.tech_innovation_score:.1f} | 40 | 40% |")
        md.append(f"| 场景创新力 | {report.scenario_innovation_score:.1f} | 60 | 60% |")
        md.append("")
        
        # ============ 六维能力雷达图 ============
        md.append("---")
        md.append("")
        md.append("## 📈 六维能力雷达图")
        md.append("")
        md.append("*以下展示项目在6个关键维度的表现（满分100）：*")
        md.append("")
        
        # 技术创新力维度
        md.append("### 🔧 技术创新力 (40%)")
        md.append("")
        for dim in report.dimensions:
            if dim.category == "tech":
                bar_len = int(dim.score / 10)
                bar = "█" * bar_len + "░" * (10 - bar_len)
                md.append(f"- **{dim.name_cn}**: `{bar}` {dim.score:.0f}分")
        md.append("")
        
        # 场景创新力维度
        md.append("### 🎯 场景创新力 (60%)")
        md.append("")
        for dim in report.dimensions:
            if dim.category == "scenario":
                bar_len = int(dim.score / 10)
                bar = "█" * bar_len + "░" * (10 - bar_len)
                md.append(f"- **{dim.name_cn}**: `{bar}` {dim.score:.0f}分")
        md.append("")
        
        # 雷达图解读
        if report.radar_analysis:
            md.append("### 📊 能力分析解读")
            md.append("")
            md.append(report.radar_analysis)
            md.append("")
        
        # ============ 详细维度分析 ============
        md.append("---")
        md.append("")
        md.append("## 🔍 详细维度分析")
        md.append("")
        
        dim_order = [
            ("tech_implementation", "1. 技术选型与实现"),
            ("architecture_design", "2. 系统架构与设计"),
            ("engineering_sustainability", "3. 工程化与可持续性"),
            ("problem_value", "4. 问题定义与价值"),
            ("scenario_innovation", "5. 场景创新性（重点）"),
            ("market_fit", "6. 市场与生态契合度"),
        ]
        
        for dim_name, title in dim_order:
            dim = next((d for d in report.dimensions if d.name == dim_name), None)
            if dim:
                md.append(f"### {title}")
                md.append("")
                md.append(f"**得分**：{dim.score:.0f}/100（权重{dim.weight:.0f}%）")
                md.append("")
                analysis = report.dimension_analyses.get(dim_name, dim.details)
                md.append(analysis)
                md.append("")
        
        # ============ 具体改进建议 ============
        md.append("---")
        md.append("")
        md.append("## 🛠️ 具体改进建议")
        md.append("")
        
        if report.tech_suggestions:
            md.append("### 🔧 技术加固")
            md.append("")
            for i, suggestion in enumerate(report.tech_suggestions, 1):
                if isinstance(suggestion, dict):
                    md.append(f"#### 建议{i}：{suggestion.get('title')}（优先级：{suggestion.get('priority')}）")
                    md.append("")
                    md.append(f"**描述**：{suggestion.get('description')}")
                    md.append("")
                    md.append(f"**原因**：{suggestion.get('reason')}")
                    md.append("")
                    md.append("**具体措施**：")
                    md.append(suggestion.get('measures'))
                    md.append("")
                    md.append(f"**预期效果**：{suggestion.get('expected_effect')}")
                    md.append("")
                else:
                    md.append(f"{i}. {suggestion}")
                    md.append("")
        
        if report.scenario_suggestions:
            md.append("### 🎯 场景深化")
            md.append("")
            for i, suggestion in enumerate(report.scenario_suggestions, 1):
                if isinstance(suggestion, dict):
                    md.append(f"#### 建议{i}：{suggestion.get('title')}（优先级：{suggestion.get('priority')}）")
                    md.append("")
                    md.append(f"**描述**：{suggestion.get('description')}")
                    md.append("")
                    md.append(f"**原因**：{suggestion.get('reason')}")
                    md.append("")
                    md.append("**具体措施**：")
                    md.append(suggestion.get('measures'))
                    md.append("")
                    md.append(f"**预期效果**：{suggestion.get('expected_effect')}")
                    md.append("")
                else:
                    md.append(f"{i}. {suggestion}")
                    md.append("")
        
        if report.product_suggestions:
            md.append("### 📱 产品化推进")
            md.append("")
            for i, suggestion in enumerate(report.product_suggestions, 1):
                if isinstance(suggestion, dict):
                    md.append(f"#### 建议{i}：{suggestion.get('title')}（优先级：{suggestion.get('priority')}）")
                    md.append("")
                    md.append(f"**描述**：{suggestion.get('description')}")
                    md.append("")
                    md.append(f"**原因**：{suggestion.get('reason')}")
                    md.append("")
                    md.append("**具体措施**：")
                    md.append(suggestion.get('measures'))
                    md.append("")
                    md.append(f"**预期效果**：{suggestion.get('expected_effect')}")
                    md.append("")
                else:
                    md.append(f"{i}. {suggestion}")
                    md.append("")
        
        # ============ 评委灵魂拷问 ============
        md.append("---")
        md.append("")
        md.append("## 🔥 评委灵魂拷问 (The Judge Grill)")
        md.append("")
        md.append("*建议评委在评审时重点关注以下问题：*")
        md.append("")
        for i, point in enumerate(report.judge_focus_points, 1):
            if isinstance(point, dict):
                md.append(f"**Q{i}: {point.get('question')}")
                md.append("")
                md.append(f"**追问目的**：{point.get('purpose')}")
                md.append(f"**期望回答**：{point.get('expected_answer')}")
                md.append(f"**评分参考**：{point.get('scoring_criteria')}")
                md.append("")
            else:
                md.append(f"{i}. {point}")
                md.append("")
        
        # ============ 参考资料 ============
        if report.research_links:
            md.append("---")
            md.append("")
            md.append("## 🔗 参考资料链接")
            md.append("")
            links = report.research_links
            if links.get("github_repo"):
                md.append(f"- [GitHub仓库]({links['github_repo']})")
            if links.get("github_search"):
                md.append(f"- [同类项目搜索]({links['github_search']})")
            if links.get("arxiv_search"):
                md.append(f"- [相关论文搜索]({links['arxiv_search']})")
            if links.get("huggingface_search"):
                md.append(f"- [Hugging Face模型]({links['huggingface_search']})")
            md.append("")
        
        # ============ 项目健康度 ============
        md.append("---")
        md.append("")
        md.append("## 📊 项目健康度分析")
        md.append("")
        md.append(f"**社区活跃度**：{report.community_health.get('stars', 0)} Stars")
        md.append(f"**贡献者数量**：{report.community_health.get('contributors', 0)} 人")
        md.append(f"**开放问题**：{report.community_health.get('issues', 0)} 个")
        md.append("")
        
        # ============ 页脚 ============
        md.append("---")
        md.append("")
        md.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 分析耗时: {report.analysis_time:.1f}秒*")
        md.append(f"*SAGE AI创新性评估系统 v3.0（深度优化版）*")
        
        return "\n".join(md)


# 测试代码
if __name__ == "__main__":
    scorer = InnovationScorer(use_modelscope=False)
    print("InnovationScorer 初始化成功")
