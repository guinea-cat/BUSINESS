"""技术栈新颖性分析器

维度1：分析项目依赖的技术栈新颖程度
- 解析requirements.txt / pyproject.toml / package.json
- 对比技术热度表
- 计算依赖组合独特性
"""
import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import TECH_CATEGORIES


@dataclass
class TechStackResult:
    """技术栈分析结果"""
    score: float  # 0-100分
    packages: List[str]  # 检测到的包列表
    cutting_edge_packages: List[str]  # 前沿技术包
    modern_packages: List[str]  # 现代技术包
    standard_packages: List[str]  # 标准技术包
    novelty_ratio: float  # 前沿技术占比
    details: str  # 详细说明


class TechStackAnalyzer:
    """技术栈新颖性分析器"""
    
    def __init__(self, tech_hotness_path: str = None):
        """
        初始化分析器
        
        Args:
            tech_hotness_path: 技术热度表JSON文件路径
        """
        self.tech_categories = TECH_CATEGORIES
        
        # 尝试加载外部技术热度表
        if tech_hotness_path:
            try:
                with open(tech_hotness_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 转换格式
                    self.tech_categories = {
                        cat: info["packages"] 
                        for cat, info in data.items()
                    }
            except Exception as e:
                print(f"加载技术热度表失败: {e}")
    
    def _parse_package_json(self, content: str) -> List[str]:
        """
        解析package.json中的依赖
        
        Args:
            content: package.json内容
            
        Returns:
            包名列表
        """
        packages = []
        try:
            data = json.loads(content)
            # 获取dependencies
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            
            for pkg in list(deps.keys()) + list(dev_deps.keys()):
                # 处理@scope/package格式
                pkg_name = pkg.lower()
                if pkg_name.startswith("@"):
                    # @langchain/core -> langchain
                    parts = pkg_name.split("/")
                    if len(parts) >= 2:
                        packages.append(parts[0][1:])  # 去掉@
                        packages.append(parts[1])
                else:
                    packages.append(pkg_name)
        except json.JSONDecodeError:
            # 如果JSON解析失败，用正则提取
            deps_match = re.findall(r'"([a-zA-Z@][a-zA-Z0-9_/-]*)"\s*:', content)
            for dep in deps_match:
                if not dep.startswith(("version", "name", "private", "scripts", "description")):
                    packages.append(dep.lower().replace("@", "").replace("/", "-"))
        
        return list(set(packages))
    
    def _parse_requirements(self, content: str) -> List[str]:
        """
        解析requirements.txt格式的依赖
        
        Args:
            content: requirements.txt内容
            
        Returns:
            包名列表（小写）
        """
        packages = []
        for line in content.split("\n"):
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith("#"):
                continue
            # 提取包名（忽略版本号）
            match = re.match(r'^([a-zA-Z0-9_-]+)', line)
            if match:
                packages.append(match.group(1).lower().replace("-", "_").replace("_", "-"))
        
        return packages
    
    def _parse_pyproject(self, content: str) -> List[str]:
        """
        解析pyproject.toml中的依赖
        
        Args:
            content: pyproject.toml内容
            
        Returns:
            包名列表（小写）
        """
        packages = []
        
        # 简单正则提取dependencies部分的包名
        # 匹配 "package-name" 或 'package-name' 或 package-name = "..."
        patterns = [
            r'"([a-zA-Z0-9_-]+)"',
            r"'([a-zA-Z0-9_-]+')",
            r'^([a-zA-Z0-9_-]+)\s*=',
        ]
        
        in_dependencies = False
        for line in content.split("\n"):
            if "[project.dependencies]" in line or "[tool.poetry.dependencies]" in line:
                in_dependencies = True
                continue
            if in_dependencies:
                if line.startswith("["):
                    in_dependencies = False
                    continue
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        pkg = match.lower().replace("-", "_").replace("_", "-")
                        if pkg and pkg not in ["python", "^"]:
                            packages.append(pkg)
        
        # 如果上述方法没提取到，使用更宽松的匹配
        if not packages:
            all_matches = re.findall(r'([a-zA-Z][a-zA-Z0-9_-]*)\s*[=<>~!]', content)
            packages = [m.lower().replace("_", "-") for m in all_matches if len(m) > 2]
        
        return list(set(packages))
    
    def _categorize_packages(self, packages: List[str]) -> Dict[str, List[str]]:
        """
        将包分类到不同技术等级
        
        Args:
            packages: 包名列表
            
        Returns:
            分类结果 {category: [packages]}
        """
        result = {
            "cutting_edge": [],
            "modern": [],
            "standard": [],
            "basic": [],
            "unknown": [],
        }
        
        for pkg in packages:
            pkg_normalized = pkg.lower().replace("-", "_").replace("_", "-")
            categorized = False
            
            for category, category_packages in self.tech_categories.items():
                # 检查包名是否匹配（支持部分匹配）
                for cat_pkg in category_packages:
                    cat_pkg_normalized = cat_pkg.lower().replace("-", "_").replace("_", "-")
                    if pkg_normalized == cat_pkg_normalized or pkg_normalized.startswith(cat_pkg_normalized):
                        result[category].append(pkg)
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                result["unknown"].append(pkg)
        
        return result
    
    def _calculate_score(self, categorized: Dict[str, List[str]], total_packages: int) -> float:
        """
        计算技术栈新颖性得分
        
        Args:
            categorized: 分类结果
            total_packages: 总包数
            
        Returns:
            得分 0-100
        """
        if total_packages == 0:
            return 50.0  # 无依赖，给中等分
        
        # 权重
        weights = {
            "cutting_edge": 100,
            "modern": 75,
            "standard": 50,
            "basic": 30,
            "unknown": 40,  # 未知包给中等偏低分
        }
        
        total_score = 0
        for category, packages in categorized.items():
            total_score += len(packages) * weights.get(category, 40)
        
        # 归一化到0-100
        score = total_score / total_packages
        
        # 额外奖励：使用多种前沿技术
        if len(categorized["cutting_edge"]) >= 3:
            score = min(100, score + 10)
        elif len(categorized["cutting_edge"]) >= 2:
            score = min(100, score + 5)
        
        # 惩罚：只使用基础包
        if len(categorized["cutting_edge"]) == 0 and len(categorized["modern"]) == 0:
            score = max(0, score - 10)
        
        return min(100, max(0, score))
    
    def analyze(self, requirements_content: str = "", pyproject_content: str = "") -> TechStackResult:
        """
        分析技术栈新颖性
        
        Args:
            requirements_content: requirements.txt或package.json内容
            pyproject_content: pyproject.toml内容
            
        Returns:
            TechStackResult分析结果
        """
        # 解析依赖
        packages = []
        
        if requirements_content:
            # 自动检测是package.json还是requirements.txt
            content = requirements_content.strip()
            if content.startswith("{"):
                # JSON格式 - package.json
                packages.extend(self._parse_package_json(content))
            else:
                # requirements.txt格式
                packages.extend(self._parse_requirements(content))
        
        if pyproject_content:
            packages.extend(self._parse_pyproject(pyproject_content))
        
        # 去重
        packages = list(set(packages))
        
        # 分类
        categorized = self._categorize_packages(packages)
        
        # 计算得分
        score = self._calculate_score(categorized, len(packages))
        
        # 计算前沿技术占比
        cutting_edge_count = len(categorized["cutting_edge"])
        modern_count = len(categorized["modern"])
        novelty_ratio = (cutting_edge_count + modern_count * 0.5) / max(len(packages), 1)
        
        # 生成详细说明
        details_parts = []
        if categorized["cutting_edge"]:
            details_parts.append(f"前沿技术: {', '.join(categorized['cutting_edge'][:5])}")
        if categorized["modern"]:
            details_parts.append(f"现代技术: {', '.join(categorized['modern'][:5])}")
        if categorized["standard"]:
            details_parts.append(f"标准技术: {', '.join(categorized['standard'][:3])}")
        
        if not details_parts:
            if packages:
                details_parts.append(f"检测到 {len(packages)} 个依赖包")
            else:
                details_parts.append("未检测到依赖文件")
        
        return TechStackResult(
            score=score,
            packages=packages,
            cutting_edge_packages=categorized["cutting_edge"],
            modern_packages=categorized["modern"],
            standard_packages=categorized["standard"],
            novelty_ratio=novelty_ratio,
            details="; ".join(details_parts),
        )


# 测试代码
if __name__ == "__main__":
    analyzer = TechStackAnalyzer()
    
    # 测试requirements.txt解析
    test_req = """
langchain>=0.1.0
openai>=1.0.0
chromadb
streamlit
numpy
pandas
"""
    
    result = analyzer.analyze(requirements_content=test_req)
    print(f"得分: {result.score:.1f}")
    print(f"前沿技术: {result.cutting_edge_packages}")
    print(f"现代技术: {result.modern_packages}")
    print(f"详情: {result.details}")
