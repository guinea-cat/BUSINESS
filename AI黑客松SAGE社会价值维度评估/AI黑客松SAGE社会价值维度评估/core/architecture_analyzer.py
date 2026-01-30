"""架构独特性分析器

维度2：分析项目代码架构的独特程度
- 目录结构深度/广度分析
- 模块化程度评估
- 常见vs自定义架构模式检测
"""
import re
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass
from collections import Counter


@dataclass
class ArchitectureResult:
    """架构分析结果"""
    score: float  # 0-100分
    directory_depth: int  # 目录最大深度
    directory_breadth: int  # 顶层目录数
    module_count: int  # Python模块数
    has_package_structure: bool  # 是否有包结构
    detected_patterns: List[str]  # 检测到的架构模式
    is_standard_template: bool  # 是否为标准模板
    details: str  # 详细说明
    # 新增：评分透明度
    scoring_breakdown: Dict[str, Any] = None  # 评分明细
    architecture_type: str = ""  # 架构类型描述
    dependency_complexity: str = ""  # 依赖复杂度评估
    coupling_assessment: str = ""  # 耦合度评估


class ArchitectureAnalyzer:
    """架构独特性分析器"""
    
    # 常见的标准项目模板特征
    STANDARD_TEMPLATES = {
        "streamlit_simple": ["app.py", "requirements.txt"],
        "fastapi_basic": ["main.py", "requirements.txt", "routers/"],
        "flask_basic": ["app.py", "templates/", "static/"],
        "django_standard": ["manage.py", "settings.py", "urls.py"],
        "ml_notebook": [".ipynb", "data/", "notebooks/"],
        "nextjs_basic": ["pages/", "next.config", "package.json"],
    }
    
    # 高级架构特征（加分）- 扩展版
    ADVANCED_PATTERNS = {
        "microservices": {
            "markers": ["services/", "api/", "gateway/"],
            "description": "微服务架构",
            "score_bonus": 12,
        },
        "clean_architecture": {
            "markers": ["domain/", "usecases/", "interfaces/", "infrastructure/"],
            "description": "整洁架构",
            "score_bonus": 15,
        },
        "hexagonal": {
            "markers": ["adapters/", "ports/", "core/"],
            "description": "六边形架构",
            "score_bonus": 15,
        },
        "plugin_system": {
            "markers": ["plugins/", "extensions/", "addons/"],
            "description": "插件系统架构",
            "score_bonus": 10,
        },
        "multi_agent": {
            "markers": ["agents/", "orchestrator/", "tools/"],
            "description": "多智能体架构",
            "score_bonus": 12,
        },
        "mvc_pattern": {
            "markers": ["models/", "views/", "controllers/"],
            "description": "MVC模式",
            "score_bonus": 8,
        },
        "pipeline": {
            "markers": ["pipeline/", "stages/", "processors/"],
            "description": "流水线架构",
            "score_bonus": 10,
        },
        "event_driven": {
            "markers": ["events/", "handlers/", "listeners/", "subscribers/"],
            "description": "事件驱动架构",
            "score_bonus": 12,
        },
        "monorepo": {
            "markers": ["packages/", "apps/", "libs/"],
            "description": "Monorepo架构",
            "score_bonus": 8,
        },
    }
    
    def __init__(self):
        pass
    
    def _parse_directory_tree(self, tree: List[str]) -> Dict[str, Any]:
        """
        解析目录树结构
        
        Args:
            tree: 目录树字符串列表
            
        Returns:
            解析后的结构信息
        """
        max_depth = 0
        top_level_dirs = []
        all_dirs = []
        all_files = []
        python_files = []
        
        for item in tree:
            # 计算缩进深度
            stripped = item.lstrip()
            depth = (len(item) - len(stripped)) // 2
            max_depth = max(max_depth, depth)
            
            if stripped.endswith("/"):
                dir_name = stripped[:-1]
                all_dirs.append(dir_name)
                if depth == 0:
                    top_level_dirs.append(dir_name)
            else:
                all_files.append(stripped)
                if stripped.endswith(".py"):
                    python_files.append(stripped)
        
        return {
            "max_depth": max_depth,
            "top_level_dirs": top_level_dirs,
            "all_dirs": all_dirs,
            "all_files": all_files,
            "python_files": python_files,
        }
    
    def _detect_standard_template(self, structure: Dict[str, Any]) -> tuple[bool, str]:
        """
        检测是否为标准项目模板
        
        Args:
            structure: 目录结构信息
            
        Returns:
            (是否为标准模板, 模板名称)
        """
        all_items = set(structure["all_dirs"] + structure["all_files"])
        
        for template_name, markers in self.STANDARD_TEMPLATES.items():
            matches = sum(1 for m in markers if any(m in item for item in all_items))
            if matches >= len(markers) * 0.7:  # 70%匹配即认为是该模板
                return True, template_name
        
        return False, ""
    
    def _detect_advanced_patterns(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检测高级架构模式（扩展版）
        
        Args:
            structure: 目录结构信息
            
        Returns:
            检测到的模式列表（含详细信息）
        """
        detected = []
        all_dirs_lower = [d.lower() for d in structure["all_dirs"]]
        all_files_lower = [f.lower() for f in structure["all_files"]]
        
        for pattern_name, pattern_info in self.ADVANCED_PATTERNS.items():
            markers = pattern_info["markers"]
            matches = sum(1 for m in markers if any(m.rstrip("/").lower() in d for d in all_dirs_lower))
            if matches >= 2:  # 至少匹配2个特征
                detected.append({
                    "name": pattern_name,
                    "description": pattern_info["description"],
                    "score_bonus": pattern_info["score_bonus"],
                    "matched_markers": matches,
                })
        
        return detected
    
    def _analyze_dependency_complexity(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析依赖复杂度
        
        Args:
            structure: 目录结构信息
            
        Returns:
            依赖复杂度评估
        """
        all_files = structure["all_files"]
        all_dirs = structure["all_dirs"]
        
        # 检测依赖文件
        has_requirements = any("requirements" in f.lower() for f in all_files)
        has_package_json = any("package.json" in f.lower() for f in all_files)
        has_pyproject = any("pyproject.toml" in f.lower() for f in all_files)
        has_cargo = any("cargo.toml" in f.lower() for f in all_files)
        has_go_mod = any("go.mod" in f.lower() for f in all_files)
        
        # 检测多环境配置
        env_configs = sum(1 for f in all_files if any(x in f.lower() for x in 
                         ["requirements-dev", "requirements-prod", "package-lock", "yarn.lock", "pnpm-lock"]))
        
        # 检测monorepo特征
        is_monorepo = any(d.lower() in ["packages", "apps", "libs", "modules"] for d in all_dirs)
        
        complexity_level = "低"
        complexity_score = 0
        
        if is_monorepo:
            complexity_level = "高（Monorepo）"
            complexity_score = 15
        elif env_configs >= 2:
            complexity_level = "中高（多环境配置）"
            complexity_score = 10
        elif has_requirements or has_package_json:
            complexity_level = "中"
            complexity_score = 5
        
        return {
            "level": complexity_level,
            "score": complexity_score,
            "has_requirements": has_requirements,
            "has_package_json": has_package_json,
            "is_monorepo": is_monorepo,
            "env_configs": env_configs,
        }
    
    def _assess_coupling(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估代码耦合度
        
        基于目录结构推断耦合度（高内聚低耦合为佳）
        
        Args:
            structure: 目录结构信息
            
        Returns:
            耦合度评估
        """
        all_dirs = structure["all_dirs"]
        all_files = structure["all_files"]
        top_level_dirs = structure["top_level_dirs"]
        
        # 耦合度指标
        indicators = {
            "模块分离度": 0,  # 目录数/文件数比率
            "层次清晰度": 0,  # 是否有清晰的层次结构
            "关注点分离": 0,  # 是否有专门的目录（如utils, config, models等）
        }
        
        # 1. 模块分离度评估
        file_count = len(all_files)
        dir_count = len(all_dirs)
        if dir_count > 0 and file_count > 0:
            ratio = file_count / dir_count
            if ratio <= 3:
                indicators["模块分离度"] = 3  # 优秀
            elif ratio <= 5:
                indicators["模块分离度"] = 2  # 良好
            else:
                indicators["模块分离度"] = 1  # 一般
        
        # 2. 层次清晰度评估
        depth = structure["max_depth"]
        if 2 <= depth <= 4:
            indicators["层次清晰度"] = 3  # 优秀
        elif depth == 1 or depth == 5:
            indicators["层次清晰度"] = 2  # 良好
        else:
            indicators["层次清晰度"] = 1  # 一般或过深
        
        # 3. 关注点分离评估
        separation_dirs = ["utils", "config", "models", "services", "core", "lib", "helpers", "common"]
        matched = sum(1 for d in all_dirs if any(s in d.lower() for s in separation_dirs))
        if matched >= 3:
            indicators["关注点分离"] = 3
        elif matched >= 1:
            indicators["关注点分离"] = 2
        else:
            indicators["关注点分离"] = 1
        
        # 总分和评级
        total = sum(indicators.values())
        if total >= 8:
            assessment = "低耦合（优秀）"
            coupling_score = 15
        elif total >= 6:
            assessment = "中等耦合（良好）"
            coupling_score = 10
        else:
            assessment = "高耦合（需改进）"
            coupling_score = 5
        
        return {
            "assessment": assessment,
            "score": coupling_score,
            "indicators": indicators,
            "total_indicator_score": total,
        }
    
    def _calculate_modularity_score(self, structure: Dict[str, Any]) -> float:
        """
        计算模块化程度得分
        
        Args:
            structure: 目录结构信息
            
        Returns:
            模块化得分 0-100
        """
        python_files = structure["python_files"]
        all_dirs = structure["all_dirs"]
        
        if not python_files:
            return 50.0  # 无Python文件，给中等分
        
        # 检查是否有__init__.py（包结构）
        has_init = any("__init__" in f for f in python_files)
        
        # 计算文件分布均匀度
        file_count = len(python_files)
        dir_count = max(len(all_dirs), 1)
        
        # 文件/目录比率（越低表示模块化越好）
        ratio = file_count / dir_count
        
        score = 50.0  # 基础分
        
        # 有包结构加分
        if has_init:
            score += 15
        
        # 目录深度合理（2-4层）加分
        depth = structure["max_depth"]
        if 2 <= depth <= 4:
            score += 10
        elif depth > 4:
            score += 5  # 过深扣一点
        
        # 目录数量合理（3-10个）加分
        if 3 <= len(all_dirs) <= 10:
            score += 10
        elif len(all_dirs) > 10:
            score += 5
        
        # 文件分布合理
        if 1 <= ratio <= 5:
            score += 10
        
        return min(100, max(0, score))
    
    def analyze(self, directory_tree: List[str], python_files: List[str] = None) -> ArchitectureResult:
        """
        分析架构独特性（增强版）
        
        Args:
            directory_tree: 目录树列表
            python_files: Python文件列表（可选，用于补充）
            
        Returns:
            ArchitectureResult分析结果
        """
        # 解析目录结构
        structure = self._parse_directory_tree(directory_tree)
        
        # 补充Python文件信息
        if python_files:
            structure["python_files"].extend([f for f in python_files if f not in structure["python_files"]])
        
        # 初始化评分明细
        scoring_breakdown = {
            "基础分": 30.0,
            "模块化得分": 0.0,
            "架构模式加分": 0.0,
            "依赖复杂度分": 0.0,
            "耦合度评分": 0.0,
            "标准模板扣分": 0.0,
        }
        
        # 检测标准模板
        is_template, template_name = self._detect_standard_template(structure)
        
        # 检测高级架构模式（扩展版）
        advanced_patterns = self._detect_advanced_patterns(structure)
        pattern_names = [p["name"] for p in advanced_patterns]
        pattern_descriptions = [p["description"] for p in advanced_patterns]
        
        # 计算模块化得分
        modularity_score = self._calculate_modularity_score(structure)
        scoring_breakdown["模块化得分"] = min(25, (modularity_score - 50) / 2)  # 转换为0-25分
        
        # 分析依赖复杂度
        dep_analysis = self._analyze_dependency_complexity(structure)
        scoring_breakdown["依赖复杂度分"] = dep_analysis["score"]
        
        # 评估耦合度
        coupling_analysis = self._assess_coupling(structure)
        scoring_breakdown["耦合度评分"] = coupling_analysis["score"]
        
        # 架构模式加分
        pattern_bonus = sum(p["score_bonus"] for p in advanced_patterns)
        scoring_breakdown["架构模式加分"] = min(20, pattern_bonus)  # 最多20分
        
        # 标准模板扣分
        if is_template:
            scoring_breakdown["标准模板扣分"] = -15
        
        # 计算最终得分
        score = sum(scoring_breakdown.values())
        score = min(100, max(0, score))
        
        # 生成架构类型描述
        if pattern_descriptions:
            architecture_type = f"采用{' + '.join(pattern_descriptions)}"
        elif is_template:
            architecture_type = f"标准{template_name}模板"
        else:
            architecture_type = "常规项目结构"
        
        # 生成详细说明
        details_parts = []
        details_parts.append(f"目录深度: {structure['max_depth']}层")
        details_parts.append(f"模块数: {len(structure['all_dirs'])}个")
        details_parts.append(f"耦合度: {coupling_analysis['assessment']}")
        
        if is_template:
            details_parts.append(f"检测到标准模板: {template_name}")
        
        if pattern_descriptions:
            details_parts.append(f"架构模式: {', '.join(pattern_descriptions)}")
        
        return ArchitectureResult(
            score=score,
            directory_depth=structure["max_depth"],
            directory_breadth=len(structure["top_level_dirs"]),
            module_count=len(structure["all_dirs"]),
            has_package_structure=any("__init__" in f for f in structure["python_files"]),
            detected_patterns=pattern_names,
            is_standard_template=is_template,
            details="; ".join(details_parts),
            # 新增字段
            scoring_breakdown=scoring_breakdown,
            architecture_type=architecture_type,
            dependency_complexity=dep_analysis["level"],
            coupling_assessment=coupling_analysis["assessment"],
        )


# 测试代码
if __name__ == "__main__":
    analyzer = ArchitectureAnalyzer()
    
    # 测试目录树
    test_tree = [
        "src/",
        "  agents/",
        "    __init__.py",
        "    base_agent.py",
        "    rag_agent.py",
        "  core/",
        "    __init__.py",
        "    engine.py",
        "  utils/",
        "    __init__.py",
        "    helpers.py",
        "app.py",
        "requirements.txt",
        "README.md",
    ]
    
    result = analyzer.analyze(test_tree)
    print(f"得分: {result.score:.1f}")
    print(f"目录深度: {result.directory_depth}")
    print(f"检测到的模式: {result.detected_patterns}")
    print(f"详情: {result.details}")
