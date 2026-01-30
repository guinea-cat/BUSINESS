"""问题解决路径新颖性分析器

维度5：分析项目解决问题的方法新颖程度
- README语义分析
- 问题描述和解决方案提取
- 跨领域创新关键词检测
"""
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class SolutionResult:
    """问题解决路径分析结果"""
    score: float  # 0-100分
    problem_clarity: float  # 问题描述清晰度
    solution_uniqueness: float  # 解决方案独特性
    cross_domain: bool  # 是否跨领域
    innovation_keywords: List[str]  # 创新关键词
    domain_tags: List[str]  # 领域标签
    details: str  # 详细说明
    # 新增：评分透明度
    scoring_breakdown: Dict[str, Any] = None  # 评分明细
    readme_quality: Dict[str, Any] = None  # README质量分析
    clarity_explanation: str = ""  # 清晰度评分解释
    uniqueness_explanation: str = ""  # 独特性评分解释


class SolutionAnalyzer:
    """问题解决路径新颖性分析器"""
    
    # 创新性关键词（高价值）
    INNOVATION_KEYWORDS = [
        "novel", "innovative", "breakthrough", "first", "unique",
        "state-of-the-art", "cutting-edge", "pioneering", "revolutionary",
        "创新", "首创", "突破", "独创", "领先", "原创",
        "新颖", "前沿", "开创性", "革命性",
    ]
    
    # 领域关键词
    DOMAIN_KEYWORDS = {
        "nlp": ["nlp", "natural language", "text", "语言", "文本", "对话", "chatbot"],
        "cv": ["computer vision", "image", "video", "视觉", "图像", "视频", "检测"],
        "ml": ["machine learning", "deep learning", "neural", "机器学习", "深度学习", "神经网络"],
        "rag": ["rag", "retrieval", "knowledge base", "检索", "知识库", "向量"],
        "agent": ["agent", "autonomous", "multi-agent", "智能体", "代理", "自主"],
        "audio": ["audio", "speech", "voice", "音频", "语音", "声音"],
        "recommendation": ["recommendation", "personalization", "推荐", "个性化"],
        "automation": ["automation", "workflow", "pipeline", "自动化", "工作流"],
    }
    
    # 跨领域组合（高创新指示）
    CROSS_DOMAIN_PAIRS = [
        ("nlp", "cv"),  # 多模态
        ("agent", "rag"),  # RAG Agent
        ("audio", "nlp"),  # 语音对话
        ("ml", "automation"),  # AutoML
    ]
    
    # 问题描述模式
    PROBLEM_PATTERNS = [
        r"(?:problem|challenge|issue|difficulty)[:\s]+(.+?)(?:\.|$)",
        r"(?:解决|处理|应对)[了的]?(.+?)(?:问题|挑战|难题)",
        r"(?:痛点|需求)[:\s]*(.+?)(?:\.|。|$)",
        r"(?:we address|we solve|we tackle)(.+?)(?:\.|$)",
    ]
    
    # 解决方案模式
    SOLUTION_PATTERNS = [
        r"(?:solution|approach|method)[:\s]+(.+?)(?:\.|$)",
        r"(?:we propose|we present|we introduce)(.+?)(?:\.|$)",
        r"(?:通过|采用|使用|利用)(.+?)(?:来|以|实现)",
        r"(?:本项目|该系统|我们)(.+?)(?:\.|。|$)",
    ]
    
    def __init__(self, similarity_calculator=None):
        """
        初始化分析器
        
        Args:
            similarity_calculator: 相似度计算器（可选）
        """
        self.similarity_calculator = similarity_calculator
    
    def _extract_text_sections(self, readme: str) -> Dict[str, str]:
        """
        提取README中的各个部分
        
        Args:
            readme: README内容
            
        Returns:
            各部分内容 {section_name: content}
        """
        sections = {
            "title": "",
            "description": "",
            "features": "",
            "usage": "",
            "full_text": readme,
        }
        
        lines = readme.split("\n")
        current_section = "description"
        section_content = []
        
        for line in lines:
            # 检测标题
            if line.startswith("# "):
                sections["title"] = line[2:].strip()
            elif line.startswith("## "):
                # 保存上一个section
                if section_content:
                    sections[current_section] = "\n".join(section_content)
                    section_content = []
                
                # 识别新section
                header = line[3:].lower().strip()
                if "feature" in header or "功能" in header:
                    current_section = "features"
                elif "usage" in header or "使用" in header or "getting started" in header:
                    current_section = "usage"
                elif "介绍" in header or "about" in header or "introduction" in header:
                    current_section = "description"
            else:
                section_content.append(line)
        
        # 保存最后一个section
        if section_content:
            sections[current_section] = "\n".join(section_content)
        
        return sections
    
    def _detect_innovation_keywords(self, text: str) -> List[str]:
        """
        检测创新性关键词
        
        Args:
            text: 文本内容
            
        Returns:
            检测到的关键词列表
        """
        text_lower = text.lower()
        found = []
        
        for keyword in self.INNOVATION_KEYWORDS:
            if keyword.lower() in text_lower:
                found.append(keyword)
        
        return list(set(found))
    
    def _detect_domains(self, text: str) -> List[str]:
        """
        检测涉及的技术领域
        
        Args:
            text: 文本内容
            
        Returns:
            领域标签列表
        """
        text_lower = text.lower()
        domains = []
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                domains.append(domain)
        
        return domains
    
    def _is_cross_domain(self, domains: List[str]) -> bool:
        """
        判断是否为跨领域项目
        
        Args:
            domains: 领域列表
            
        Returns:
            是否跨领域
        """
        domain_set = set(domains)
        
        for pair in self.CROSS_DOMAIN_PAIRS:
            if pair[0] in domain_set and pair[1] in domain_set:
                return True
        
        return len(domains) >= 3  # 涉及3个以上领域也算跨领域
    
    def _calculate_problem_clarity(self, text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        计算问题描述清晰度（增强版，透明化评分）
        
        Args:
            text: 文本内容
            sections: README各部分
            
        Returns:
            清晰度分析结果（含评分明细）
        """
        breakdown = {
            "有问题/挑战描述": {"score": 0, "max": 20, "found": False},
            "有使用场景说明": {"score": 0, "max": 15, "found": False},
            "有目标用户描述": {"score": 0, "max": 15, "found": False},
            "有背景/动机说明": {"score": 0, "max": 15, "found": False},
            "README结构完整": {"score": 0, "max": 20, "found": False},
            "描述长度适中": {"score": 0, "max": 15, "found": False},
        }
        
        text_lower = text.lower()
        
        # 1. 检测问题描述关键词
        problem_indicators = ["problem", "challenge", "issue", "solve", "address", "pain point",
                            "问题", "挑战", "解决", "痛点", "需求", "困难"]
        if any(ind in text_lower for ind in problem_indicators):
            breakdown["有问题/挑战描述"]["score"] = 20
            breakdown["有问题/挑战描述"]["found"] = True
        
        # 2. 检测使用场景描述
        scenario_indicators = ["use case", "scenario", "application", "example", "demo",
                            "场景", "应用", "用途", "示例", "案例"]
        if any(ind in text_lower for ind in scenario_indicators):
            breakdown["有使用场景说明"]["score"] = 15
            breakdown["有使用场景说明"]["found"] = True
        
        # 3. 检测目标用户描述
        user_indicators = ["user", "developer", "researcher", "team", "enterprise", "for",
                         "用户", "开发者", "研究者", "团队", "企业", "适合"]
        if any(ind in text_lower for ind in user_indicators):
            breakdown["有目标用户描述"]["score"] = 15
            breakdown["有目标用户描述"]["found"] = True
        
        # 4. 检测背景/动机说明
        background_indicators = ["background", "motivation", "why", "introduction", "overview",
                               "背景", "动机", "为什么", "介绍", "概述"]
        if any(ind in text_lower for ind in background_indicators):
            breakdown["有背景/动机说明"]["score"] = 15
            breakdown["有背景/动机说明"]["found"] = True
        
        # 5. README结构完整性检测
        readme_sections = []
        section_keywords = {
            "title": ["# "],
            "description": ["introduction", "about", "overview", "介绍", "简介"],
            "features": ["feature", "功能", "特性"],
            "installation": ["install", "setup", "getting started", "安装", "开始"],
            "usage": ["usage", "how to", "example", "使用", "示例"],
        }
        
        for section_name, keywords in section_keywords.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    readme_sections.append(section_name)
                    break
        
        section_score = min(20, len(set(readme_sections)) * 5)
        breakdown["README结构完整"]["score"] = section_score
        breakdown["README结构完整"]["found"] = len(set(readme_sections)) >= 3
        
        # 6. 描述长度评估
        if 800 <= len(text) <= 3000:
            breakdown["描述长度适中"]["score"] = 15
            breakdown["描述长度适中"]["found"] = True
        elif 400 <= len(text) <= 5000:
            breakdown["描述长度适中"]["score"] = 10
            breakdown["描述长度适中"]["found"] = True
        elif len(text) > 200:
            breakdown["描述长度适中"]["score"] = 5
        
        # 计算总分（转换为0-1）
        total_score = sum(item["score"] for item in breakdown.values())
        max_score = sum(item["max"] for item in breakdown.values())
        clarity_score = total_score / max_score if max_score > 0 else 0
        
        # 生成解释
        found_items = [k for k, v in breakdown.items() if v["found"]]
        missing_items = [k for k, v in breakdown.items() if not v["found"]]
        
        explanation = f"检测到: {', '.join(found_items) if found_items else '无'}"
        if missing_items:
            explanation += f"；建议补充: {', '.join(missing_items[:2])}"
        
        return {
            "score": clarity_score,
            "breakdown": breakdown,
            "explanation": explanation,
            "readme_sections": list(set(readme_sections)),
        }
    
    def _calculate_solution_uniqueness(self, text: str, domains: List[str], 
                                       innovation_keywords: List[str]) -> Dict[str, Any]:
        """
        计算解决方案独特性（增强版，透明化评分）
        
        Args:
            text: 文本内容
            domains: 涉及领域
            innovation_keywords: 创新关键词
            
        Returns:
            独特性分析结果（含评分明细）
        """
        breakdown = {
            "创新关键词": {"score": 0, "max": 25, "details": ""},
            "多领域融合": {"score": 0, "max": 20, "details": ""},
            "技术方案描述": {"score": 0, "max": 20, "details": ""},
            "差异化对比": {"score": 0, "max": 20, "details": ""},
            "量化指标": {"score": 0, "max": 15, "details": ""},
        }
        
        text_lower = text.lower()
        
        # 1. 创新关键词加分
        keyword_score = min(25, len(innovation_keywords) * 8)
        breakdown["创新关键词"]["score"] = keyword_score
        breakdown["创新关键词"]["details"] = f"检测到{len(innovation_keywords)}个: {', '.join(innovation_keywords[:3])}" if innovation_keywords else "未检测到"
        
        # 2. 多领域融合加分
        if len(domains) >= 3:
            breakdown["多领域融合"]["score"] = 20
            breakdown["多领域融合"]["details"] = f"融合{len(domains)}个领域"
        elif len(domains) >= 2:
            breakdown["多领域融合"]["score"] = 15
            breakdown["多领域融合"]["details"] = f"涉及{len(domains)}个领域"
        elif len(domains) == 1:
            breakdown["多领域融合"]["score"] = 5
            breakdown["多领域融合"]["details"] = f"单一领域: {domains[0]}"
        else:
            breakdown["多领域融合"]["details"] = "未明确领域"
        
        # 3. 技术方案描述
        tech_indicators = ["algorithm", "model", "architecture", "pipeline", "framework", "method",
                         "算法", "模型", "架构", "流程", "框架", "方法", "技术"]
        tech_found = [ind for ind in tech_indicators if ind in text_lower]
        if len(tech_found) >= 3:
            breakdown["技术方案描述"]["score"] = 20
        elif len(tech_found) >= 1:
            breakdown["技术方案描述"]["score"] = 10
        breakdown["技术方案描述"]["details"] = f"技术词汇: {', '.join(tech_found[:3])}" if tech_found else "缺少技术描述"
        
        # 4. 差异化对比（与现有方案对比）
        comparison_indicators = ["compared to", "unlike", "different from", "improve", "better than",
                                "vs", "versus", "相比", "不同于", "改进", "优于", "区别"]
        comparison_found = any(ind in text_lower for ind in comparison_indicators)
        if comparison_found:
            breakdown["差异化对比"]["score"] = 20
            breakdown["差异化对比"]["details"] = "有与现有方案的对比说明"
        else:
            breakdown["差异化对比"]["details"] = "建议添加与同类方案的差异化描述"
        
        # 5. 量化指标
        quantitative_patterns = [
            r'\d+%', r'\d+x', r'\d+倍', r'\d+ms', r'\d+秒',
            r'accuracy', r'precision', r'recall', r'f1',
            r'准确率', r'性能', r'效率'
        ]
        quantitative_found = any(re.search(p, text_lower) for p in quantitative_patterns)
        if quantitative_found:
            breakdown["量化指标"]["score"] = 15
            breakdown["量化指标"]["details"] = "有性能/效果量化数据"
        else:
            breakdown["量化指标"]["details"] = "建议添加量化效果指标"
        
        # 计算总分（转换为0-1）
        total_score = sum(item["score"] for item in breakdown.values())
        max_score = sum(item["max"] for item in breakdown.values())
        uniqueness_score = total_score / max_score if max_score > 0 else 0
        
        # 生成解释
        good_items = [k for k, v in breakdown.items() if v["score"] >= v["max"] * 0.5]
        explanation = f"得分项: {', '.join(good_items)}" if good_items else "独特性描述较弱"
        
        return {
            "score": uniqueness_score,
            "breakdown": breakdown,
            "explanation": explanation,
        }
    
    def _calculate_score(self, problem_clarity: float, solution_uniqueness: float,
                        is_cross_domain: bool, innovation_count: int) -> float:
        """
        计算综合得分
        
        Args:
            problem_clarity: 问题清晰度
            solution_uniqueness: 解决方案独特性
            is_cross_domain: 是否跨领域
            innovation_count: 创新关键词数量
            
        Returns:
            综合得分 0-100
        """
        # 基础分计算
        score = (problem_clarity * 30 + solution_uniqueness * 40)
        
        # 跨领域加分
        if is_cross_domain:
            score += 15
        
        # 创新关键词加分
        score += min(15, innovation_count * 5)
        
        return min(100, max(0, score))
    
    def analyze(self, readme_content: str, code_comments: str = "") -> SolutionResult:
        """
        分析问题解决路径新颖性（增强版）
        
        Args:
            readme_content: README内容
            code_comments: 代码注释（可选）
            
        Returns:
            SolutionResult分析结果
        """
        # 合并分析文本
        full_text = readme_content + "\n" + code_comments
        
        if not full_text.strip():
            return SolutionResult(
                score=30.0,
                problem_clarity=0.0,
                solution_uniqueness=0.0,
                cross_domain=False,
                innovation_keywords=[],
                domain_tags=[],
                details="未检测到README或项目描述",
                scoring_breakdown={"基础分": 30.0},
                readme_quality={"sections": [], "length": 0},
                clarity_explanation="未检测到README或项目描述",
                uniqueness_explanation="无法评估",
            )
        
        # 提取各部分
        sections = self._extract_text_sections(readme_content)
        
        # 检测创新关键词
        innovation_keywords = self._detect_innovation_keywords(full_text)
        
        # 检测涉及领域
        domains = self._detect_domains(full_text)
        
        # 判断是否跨领域
        is_cross_domain = self._is_cross_domain(domains)
        
        # 计算问题清晰度（使用增强版方法）
        clarity_result = self._calculate_problem_clarity(
            sections.get("description", "") + sections.get("title", "") + sections.get("full_text", ""),
            sections
        )
        problem_clarity = clarity_result["score"]
        
        # 计算解决方案独特性（使用增强版方法）
        uniqueness_result = self._calculate_solution_uniqueness(
            full_text, domains, innovation_keywords
        )
        solution_uniqueness = uniqueness_result["score"]
        
        # 构建综合评分明细
        scoring_breakdown = {
            "问题清晰度得分": round(problem_clarity * 40, 1),  # 最高40分
            "方案独特性得分": round(solution_uniqueness * 40, 1),  # 最高40分
            "跨领域融合加分": 15 if is_cross_domain else 0,
            "创新关键词加分": min(5, len(innovation_keywords) * 2),
        }
        
        # 计算综合得分
        score = sum(scoring_breakdown.values())
        score = min(100, max(0, score))
        
        # 生成详细说明
        details_parts = []
        if domains:
            details_parts.append(f"涉及领域: {', '.join(domains)}")
        if is_cross_domain:
            details_parts.append("跨领域融合")
        if innovation_keywords:
            details_parts.append(f"创新关键词: {', '.join(innovation_keywords[:3])}")
        
        if not details_parts:
            details_parts.append("问题定义和解决方案描述待完善")
        
        return SolutionResult(
            score=score,
            problem_clarity=problem_clarity,
            solution_uniqueness=solution_uniqueness,
            cross_domain=is_cross_domain,
            innovation_keywords=innovation_keywords,
            domain_tags=domains,
            details="; ".join(details_parts),
            # 新增透明度字段
            scoring_breakdown=scoring_breakdown,
            readme_quality={
                "sections": clarity_result.get("readme_sections", []),
                "length": len(full_text),
                "has_structure": len(clarity_result.get("readme_sections", [])) >= 3,
            },
            clarity_explanation=clarity_result.get("explanation", ""),
            uniqueness_explanation=uniqueness_result.get("explanation", ""),
        )


# 测试代码
if __name__ == "__main__":
    analyzer = SolutionAnalyzer()
    
    test_readme = """
# Multi-Modal RAG Agent

## Introduction
This project presents a novel approach to combining retrieval-augmented generation with 
multi-agent systems for complex question answering tasks.

## Problem
Traditional RAG systems struggle with multi-hop reasoning and complex queries that require
information from multiple sources. We address this challenge by introducing autonomous
agents that can plan, retrieve, and synthesize information.

## Features
- Innovative multi-agent architecture
- State-of-the-art retrieval system
- Cross-modal understanding (text + images)
- Automatic query decomposition

## Usage
pip install multi-modal-rag-agent
"""
    
    result = analyzer.analyze(test_readme)
    print(f"得分: {result.score:.1f}")
    print(f"问题清晰度: {result.problem_clarity:.2f}")
    print(f"方案独特性: {result.solution_uniqueness:.2f}")
    print(f"跨领域: {result.cross_domain}")
    print(f"领域: {result.domain_tags}")
    print(f"创新关键词: {result.innovation_keywords}")
    print(f"详情: {result.details}")
