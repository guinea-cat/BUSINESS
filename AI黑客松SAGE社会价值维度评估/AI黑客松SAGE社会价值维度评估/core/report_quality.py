"""报告质量评估模块

提供报告质量评估功能，确保生成的评估报告符合专业标准和质量要求。
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class QualityMetric:
    """质量评估指标"""
    name: str  # 指标名称
    description: str  # 指标描述
    weight: float  # 权重 0-1
    score: float  # 得分 0-100
    details: str  # 详细说明


@dataclass
class ReportQualityResult:
    """报告质量评估结果"""
    overall_score: float  # 总体质量得分 0-100
    metrics: List[QualityMetric]  # 各项指标得分
    suggestions: List[str]  # 改进建议
    is_qualified: bool  # 是否合格


class ReportQualityEvaluator:
    """报告质量评估器"""
    
    # 质量评估指标配置
    QUALITY_METRICS = [
        {
            "name": "completeness",
            "description": "报告完整性",
            "weight": 0.25,
            "min_sections": 8,  # 最小章节数
            "required_sections": [
                "开篇总览", "创新性总评", "六维能力雷达图",
                "详细维度分析", "具体改进建议", "评委关注点"
            ]
        },
        {
            "name": "depth",
            "description": "分析深度",
            "weight": 0.30,
            "min_word_count": 2000,  # 最小字数
            "min_detail_length": 150,  # 每个维度最小详细分析长度
        },
        {
            "name": "professionalism",
            "description": "专业性",
            "weight": 0.20,
            "required_elements": [
                "评分分析", "维度解读", "改进建议", 
                "评委问题", "优先级评估"
            ]
        },
        {
            "name": "clarity",
            "description": "表达清晰度",
            "weight": 0.15,
            "readability_threshold": 0.7,  # 可读性阈值
        },
        {
            "name": "structure",
            "description": "结构合理性",
            "weight": 0.10,
            "required_structure": [
                "总览", "评估", "分析", "建议", "关注点"
            ]
        }
    ]
    
    def _evaluate_completeness(self, report_content: str) -> Dict[str, Any]:
        """评估报告完整性"""
        metric_config = next(m for m in self.QUALITY_METRICS if m["name"] == "completeness")
        
        # 检查章节数
        sections = re.findall(r'^#{1,6}\s+(.*?)$', report_content, re.MULTILINE)
        section_count = len(sections)
        
        # 检查必要章节
        required_sections = metric_config["required_sections"]
        found_sections = []
        missing_sections = []
        
        for section in required_sections:
            if any(section in s for s in sections):
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        # 计算得分
        section_score = min(100, (section_count / metric_config["min_sections"]) * 100)
        required_score = (len(found_sections) / len(required_sections)) * 100
        total_score = (section_score * 0.4) + (required_score * 0.6)
        
        details = f"章节数: {section_count}/{metric_config['min_sections']}, "
        details += f"必要章节: {len(found_sections)}/{len(required_sections)}"
        if missing_sections:
            details += f"，缺失章节: {', '.join(missing_sections)}"
        
        return {
            "score": total_score,
            "details": details,
            "suggestions": [f"添加缺失的章节: {', '.join(missing_sections)}"] if missing_sections else []
        }
    
    def _evaluate_depth(self, report_content: str) -> Dict[str, Any]:
        """评估分析深度"""
        metric_config = next(m for m in self.QUALITY_METRICS if m["name"] == "depth")
        
        # 计算总字数
        word_count = len(report_content.split())
        
        # 检查维度分析长度
        dimension_patterns = [
            r'技术选型与实现.*?(?=系统架构与设计|$)',
            r'系统架构与设计.*?(?=工程化与可持续性|$)',
            r'工程化与可持续性.*?(?=问题定义与价值|$)',
            r'问题定义与价值.*?(?=场景创新性|$)',
            r'场景创新性.*?(?=市场与生态契合度|$)',
            r'市场与生态契合度.*?(?=具体改进建议|$)'
        ]
        
        short_dimensions = []
        for i, pattern in enumerate(dimension_patterns):
            match = re.search(pattern, report_content, re.DOTALL)
            if match:
                content = match.group(0)
                if len(content.split()) < metric_config["min_detail_length"]:
                    short_dimensions.append([
                        "技术选型与实现", "系统架构与设计", "工程化与可持续性",
                        "问题定义与价值", "场景创新性", "市场与生态契合度"
                    ][i])
        
        # 计算得分
        word_score = min(100, (word_count / metric_config["min_word_count"]) * 100)
        detail_score = (1 - len(short_dimensions) / 6) * 100
        total_score = (word_score * 0.6) + (detail_score * 0.4)
        
        details = f"总字数: {word_count}/{metric_config['min_word_count']}, "
        details += f"简短维度: {len(short_dimensions)}/6"
        if short_dimensions:
            details += f"，维度: {', '.join(short_dimensions)}"
        
        suggestions = []
        if word_count < metric_config["min_word_count"]:
            suggestions.append(f"增加报告长度，建议至少{metric_config['min_word_count']}字")
        if short_dimensions:
            suggestions.append(f"增加以下维度的分析深度: {', '.join(short_dimensions)}")
        
        return {
            "score": total_score,
            "details": details,
            "suggestions": suggestions
        }
    
    def _evaluate_professionalism(self, report_content: str) -> Dict[str, Any]:
        """评估专业性"""
        metric_config = next(m for m in self.QUALITY_METRICS if m["name"] == "professionalism")
        
        # 检查专业元素
        required_elements = metric_config["required_elements"]
        found_elements = []
        missing_elements = []
        
        element_patterns = {
            "评分分析": r'总体评分.*?/100',
            "维度解读": r'雷达图解读|优势和短板',
            "改进建议": r'具体改进建议',
            "评委问题": r'评委关注点',
            "优先级评估": r'优先级.*?(高|中|低)'
        }
        
        for element, pattern in element_patterns.items():
            if re.search(pattern, report_content, re.IGNORECASE):
                found_elements.append(element)
            else:
                missing_elements.append(element)
        
        # 检查专业术语使用
        technical_terms = [
            "技术创新力", "场景创新力", "架构设计", "工程化",
            "创新性", "维度分析", "改进建议", "评委关注点"
        ]
        term_count = sum(1 for term in technical_terms if term in report_content)
        
        # 计算得分
        element_score = (len(found_elements) / len(required_elements)) * 100
        term_score = min(100, (term_count / len(technical_terms)) * 100)
        total_score = (element_score * 0.7) + (term_score * 0.3)
        
        details = f"专业元素: {len(found_elements)}/{len(required_elements)}, "
        details += f"专业术语: {term_count}/{len(technical_terms)}"
        if missing_elements:
            details += f"，缺失元素: {', '.join(missing_elements)}"
        
        suggestions = []
        if missing_elements:
            suggestions.append(f"添加缺失的专业元素: {', '.join(missing_elements)}")
        if term_count < len(technical_terms) * 0.7:
            suggestions.append("增加专业术语的使用，提升报告专业性")
        
        return {
            "score": total_score,
            "details": details,
            "suggestions": suggestions
        }
    
    def _evaluate_clarity(self, report_content: str) -> Dict[str, Any]:
        """评估表达清晰度"""
        metric_config = next(m for m in self.QUALITY_METRICS if m["name"] == "clarity")
        
        # 检查结构清晰度
        structure_patterns = [
            r'^#{1,6}\s+.*?$',  # 标题
            r'^-\s+.*?$',  # 列表项
            r'^\|.*?\|$',  # 表格
        ]
        
        structure_elements = 0
        for pattern in structure_patterns:
            structure_elements += len(re.findall(pattern, report_content, re.MULTILINE))
        
        # 检查语言清晰度
        # 简单的可读性评估：句子长度和标点使用
        sentences = re.split(r'[。！？.!?]', report_content)
        avg_sentence_length = sum(len(sentence.split()) for sentence in sentences if sentence.strip()) / len(sentences) if sentences else 0
        
        # 检查格式一致性
        format_issues = []
        # 检查标题层级一致性
        headers = re.findall(r'^(#+)\s+', report_content, re.MULTILINE)
        if headers:
            header_levels = [len(h) for h in headers]
            if max(header_levels) - min(header_levels) > 3:
                format_issues.append("标题层级过多")
        
        # 计算得分
        structure_score = min(100, (structure_elements / 50) * 100)  # 假设至少50个结构元素
        readability_score = max(0, 100 - (avg_sentence_length - 15) * 2)  # 理想句子长度15词
        format_score = 100 - len(format_issues) * 20  # 每个格式问题扣20分
        
        total_score = (structure_score * 0.4) + (readability_score * 0.4) + (format_score * 0.2)
        
        details = f"结构元素: {structure_elements}, "
        details += f"平均句子长度: {avg_sentence_length:.1f}, "
        details += f"格式问题: {len(format_issues)}"
        if format_issues:
            details += f"，问题: {', '.join(format_issues)}"
        
        suggestions = []
        if structure_elements < 30:
            suggestions.append("增加结构化元素（标题、列表、表格），提升可读性")
        if avg_sentence_length > 25:
            suggestions.append("简化句子结构，缩短句子长度，提升表达清晰度")
        if format_issues:
            suggestions.append(f"修复格式问题: {', '.join(format_issues)}")
        
        return {
            "score": total_score,
            "details": details,
            "suggestions": suggestions
        }
    
    def _evaluate_structure(self, report_content: str) -> Dict[str, Any]:
        """评估结构合理性"""
        metric_config = next(m for m in self.QUALITY_METRICS if m["name"] == "structure")
        
        # 检查结构流畅性
        required_structure = metric_config["required_structure"]
        
        # 分析章节顺序
        sections = re.findall(r'^#{1,3}\s+(.*?)$', report_content, re.MULTILINE)
        section_names = [s.strip() for s in sections]
        
        # 检查逻辑流程
        logical_flow_patterns = [
            ("开篇总览", "创新性总评"),
            ("创新性总评", "六维能力雷达图"),
            ("六维能力雷达图", "详细维度分析"),
            ("详细维度分析", "具体改进建议"),
            ("具体改进建议", "评委关注点")
        ]
        
        flow_issues = []
        for i, (prev, next_sec) in enumerate(logical_flow_patterns):
            prev_idx = next((j for j, s in enumerate(section_names) if prev in s), -1)
            next_idx = next((j for j, s in enumerate(section_names) if next_sec in s), -1)
            if prev_idx == -1 or next_idx == -1:
                flow_issues.append(f"缺少必要章节: {prev} 或 {next_sec}")
            elif prev_idx >= next_idx:
                flow_issues.append(f"章节顺序错误: {prev} 应在 {next_sec} 之前")
        
        # 计算得分
        flow_score = 100 - len(flow_issues) * 20  # 每个流程问题扣20分
        structure_score = min(100, (len(sections) / 10) * 100)  # 假设至少10个章节
        
        total_score = (flow_score * 0.6) + (structure_score * 0.4)
        
        details = f"章节数: {len(sections)}, "
        details += f"流程问题: {len(flow_issues)}"
        if flow_issues:
            details += f"，问题: {', '.join(flow_issues)}"
        
        suggestions = []
        if flow_issues:
            suggestions.extend(flow_issues)
        if len(sections) < 8:
            suggestions.append("增加章节数量，完善报告结构")
        
        return {
            "score": total_score,
            "details": details,
            "suggestions": suggestions
        }
    
    def evaluate(self, report_content: str) -> ReportQualityResult:
        """
        评估报告质量
        
        Args:
            report_content: 报告内容
            
        Returns:
            ReportQualityResult: 质量评估结果
        """
        metrics = []
        all_suggestions = []
        
        # 评估各项指标
        completeness_result = self._evaluate_completeness(report_content)
        metrics.append(QualityMetric(
            name="completeness",
            description="报告完整性",
            weight=0.25,
            score=completeness_result["score"],
            details=completeness_result["details"]
        ))
        all_suggestions.extend(completeness_result.get("suggestions", []))
        
        depth_result = self._evaluate_depth(report_content)
        metrics.append(QualityMetric(
            name="depth",
            description="分析深度",
            weight=0.30,
            score=depth_result["score"],
            details=depth_result["details"]
        ))
        all_suggestions.extend(depth_result.get("suggestions", []))
        
        professionalism_result = self._evaluate_professionalism(report_content)
        metrics.append(QualityMetric(
            name="professionalism",
            description="专业性",
            weight=0.20,
            score=professionalism_result["score"],
            details=professionalism_result["details"]
        ))
        all_suggestions.extend(professionalism_result.get("suggestions", []))
        
        clarity_result = self._evaluate_clarity(report_content)
        metrics.append(QualityMetric(
            name="clarity",
            description="表达清晰度",
            weight=0.15,
            score=clarity_result["score"],
            details=clarity_result["details"]
        ))
        all_suggestions.extend(clarity_result.get("suggestions", []))
        
        structure_result = self._evaluate_structure(report_content)
        metrics.append(QualityMetric(
            name="structure",
            description="结构合理性",
            weight=0.10,
            score=structure_result["score"],
            details=structure_result["details"]
        ))
        all_suggestions.extend(structure_result.get("suggestions", []))
        
        # 计算总体得分
        overall_score = sum(metric.score * metric.weight for metric in metrics)
        
        # 判断是否合格
        is_qualified = overall_score >= 70
        
        # 去重改进建议
        unique_suggestions = []
        seen = set()
        for suggestion in all_suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return ReportQualityResult(
            overall_score=overall_score,
            metrics=metrics,
            suggestions=unique_suggestions[:10],  # 最多返回10条建议
            is_qualified=is_qualified
        )
    
    def generate_quality_report(self, quality_result: ReportQualityResult) -> str:
        """
        生成质量评估报告
        
        Args:
            quality_result: 质量评估结果
            
        Returns:
            str: 质量评估报告
        """
        md = []
        
        md.append("# 报告质量评估结果")
        md.append("")
        md.append(f"## 总体评估")
        md.append("")
        md.append(f"**总体得分**: {quality_result.overall_score:.1f}/100")
        md.append(f"**评估结果**: {'合格' if quality_result.is_qualified else '不合格'}")
        md.append("")
        
        md.append("## 各项指标得分")
        md.append("")
        md.append("| 指标 | 得分 | 权重 | 加权得分 | 说明 |")
        md.append("|------|------|------|----------|------|")
        
        for metric in quality_result.metrics:
            weighted_score = metric.score * metric.weight
            md.append(f"| {metric.description} | {metric.score:.1f} | {metric.weight:.2f} | {weighted_score:.1f} | {metric.details} |")
        
        md.append("")
        
        if quality_result.suggestions:
            md.append("## 改进建议")
            md.append("")
            for i, suggestion in enumerate(quality_result.suggestions, 1):
                md.append(f"{i}. {suggestion}")
            md.append("")
        
        if not quality_result.is_qualified:
            md.append("## 不合格原因")
            md.append("")
            low_metrics = [m for m in quality_result.metrics if m.score < 60]
            if low_metrics:
                md.append("以下指标得分过低：")
                for metric in low_metrics:
                    md.append(f"- **{metric.description}**: {metric.score:.1f}/100")
            else:
                md.append("总体得分未达到合格标准")
            md.append("")
        
        md.append("## 质量标准参考")
        md.append("")
        md.append("| 得分范围 | 评价 |")
        md.append("|---------|------|")
        md.append("| 90-100 | 优秀 |")
        md.append("| 80-89 | 良好 |")
        md.append("| 70-79 | 合格 |")
        md.append("| 60-69 | 基本合格 |")
        md.append("| <60 | 不合格 |")
        
        return "\n".join(md)
