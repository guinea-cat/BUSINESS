"""核心算法创新分析器

维度3：分析代码中的核心算法创新程度
- AST解析：统计自定义函数/类数量
- 代码复杂度计算
- 语义相似度对比（调用相似度模块）
"""
import ast
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field

import sys
sys.path.append(str(Path(__file__).parent.parent))


@dataclass
class CodeAnalysisResult:
    """代码分析结果"""
    score: float  # 0-100分
    total_functions: int  # 总函数数
    total_classes: int  # 总类数
    custom_implementations: int  # 自定义实现数（非简单包装）
    avg_complexity: float  # 平均复杂度
    novelty_score: float  # 新颖性得分（与基线对比）
    key_features: List[str]  # 关键代码特征
    details: str  # 详细说明
    # 新增：评分透明度字段
    scoring_breakdown: Dict[str, Any] = None  # 评分明细
    algorithm_innovation_score: float = 0.0  # 算法创新性得分（区别于实现复杂度）
    implementation_quality_score: float = 0.0  # 实现质量得分
    novelty_explanation: str = ""  # 新颖性评分解释


class CodeAnalyzer:
    """核心算法创新分析器"""
    
    # 简单包装模式（低创新指示）
    WRAPPER_PATTERNS = [
        r"return\s+\w+\.\w+\(",  # 直接返回另一个对象的方法调用
        r"^\s*self\.\w+\s*=\s*\w+",  # 简单属性赋值
        r"^\s*pass\s*$",  # 空实现
    ]
    
    # 复杂实现模式（高创新指示）
    COMPLEX_PATTERNS = [
        r"for\s+.+\s+in\s+.+:",  # 循环
        r"while\s+.+:",  # while循环
        r"if\s+.+:",  # 条件判断
        r"try\s*:",  # 异常处理
        r"async\s+def",  # 异步函数
        r"yield\s+",  # 生成器
        r"@property",  # 属性装饰器
        r"__\w+__",  # 魔术方法
    ]
    
    def __init__(self, similarity_calculator=None):
        """
        初始化分析器
        
        Args:
            similarity_calculator: 相似度计算器实例（可选）
        """
        self.similarity_calculator = similarity_calculator
    
    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        """
        解析代码AST
        
        Args:
            code: Python代码字符串
            
        Returns:
            AST树，解析失败返回None
        """
        try:
            return ast.parse(code)
        except SyntaxError:
            return None
    
    def _count_elements(self, tree: ast.AST) -> Dict[str, int]:
        """
        统计AST中的代码元素
        
        Args:
            tree: AST树
            
        Returns:
            元素统计 {类型: 数量}
        """
        counts = {
            "functions": 0,
            "async_functions": 0,
            "classes": 0,
            "imports": 0,
            "loops": 0,
            "conditionals": 0,
            "try_blocks": 0,
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                counts["functions"] += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                counts["async_functions"] += 1
            elif isinstance(node, ast.ClassDef):
                counts["classes"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                counts["imports"] += 1
            elif isinstance(node, (ast.For, ast.While)):
                counts["loops"] += 1
            elif isinstance(node, ast.If):
                counts["conditionals"] += 1
            elif isinstance(node, ast.Try):
                counts["try_blocks"] += 1
        
        return counts
    
    def _calculate_complexity(self, code: str, tree: ast.AST) -> float:
        """
        计算代码复杂度
        
        基于McCabe复杂度的简化版本
        
        Args:
            code: 代码字符串
            tree: AST树
            
        Returns:
            复杂度分数
        """
        # 统计控制流节点
        control_flow_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, 
                                ast.ExceptHandler, ast.With, ast.Assert)):
                control_flow_count += 1
            elif isinstance(node, ast.BoolOp):  # and/or
                control_flow_count += len(node.values) - 1
        
        # 统计函数数量
        func_count = sum(1 for node in ast.walk(tree) 
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        
        # 平均每函数复杂度
        if func_count > 0:
            return control_flow_count / func_count
        return control_flow_count
    
    def _detect_custom_implementations(self, code: str) -> int:
        """
        检测自定义实现（非简单包装）
        
        Args:
            code: 代码字符串
            
        Returns:
            自定义实现数量
        """
        # 统计复杂模式出现次数
        complex_count = sum(
            len(re.findall(pattern, code, re.MULTILINE))
            for pattern in self.COMPLEX_PATTERNS
        )
        
        # 统计简单包装模式出现次数
        wrapper_count = sum(
            len(re.findall(pattern, code, re.MULTILINE))
            for pattern in self.WRAPPER_PATTERNS
        )
        
        # 自定义实现 = 复杂模式 - 简单包装
        return max(0, complex_count - wrapper_count)
    
    def _extract_key_features(self, code: str, tree: ast.AST) -> List[str]:
        """
        提取关键代码特征
        
        Args:
            code: 代码字符串
            tree: AST树
            
        Returns:
            特征列表
        """
        features = []
        
        # 检测异步编程
        async_count = sum(1 for node in ast.walk(tree) 
                         if isinstance(node, ast.AsyncFunctionDef))
        if async_count > 0:
            features.append(f"异步编程 ({async_count}个async函数)")
        
        # 检测生成器
        if "yield" in code:
            features.append("使用生成器")
        
        # 检测装饰器
        decorator_count = sum(len(node.decorator_list) for node in ast.walk(tree)
                             if isinstance(node, (ast.FunctionDef, ast.ClassDef)))
        if decorator_count > 2:
            features.append(f"使用装饰器 ({decorator_count}处)")
        
        # 检测类继承
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.bases:
                base_names = [ast.unparse(base) if hasattr(ast, 'unparse') else str(base) 
                             for base in node.bases]
                if base_names and base_names[0] not in ["object", "Exception"]:
                    features.append(f"类继承: {node.name}")
                    break
        
        # 检测魔术方法
        magic_methods = re.findall(r'def\s+(__\w+__)', code)
        if magic_methods:
            unique_magic = list(set(magic_methods))[:3]
            features.append(f"魔术方法: {', '.join(unique_magic)}")
        
        return features[:5]  # 最多返回5个特征
    
    def _calculate_score(self, counts: Dict[str, int], complexity: float, 
                        custom_impl: int, novelty: float, code: str = "") -> Dict[str, Any]:
        """
        计算综合得分（返回详细评分明细）
        
        Args:
            counts: 元素统计
            complexity: 复杂度
            custom_impl: 自定义实现数
            novelty: 新颖性得分
            code: 原始代码（用于创新性分析）
            
        Returns:
            包含得分和明细的字典
        """
        breakdown = {
            "基础分": 30.0,
            "代码规模分": 0.0,
            "复杂度分": 0.0,
            "自定义实现分": 0.0,
            "算法创新分": 0.0,
            "异步编程加分": 0.0,
            "设计模式加分": 0.0,
        }
        
        # ===== 1. 代码规模评分 (0-10分) =====
        total_defs = counts.get("functions", 0) + counts.get("async_functions", 0) + counts.get("classes", 0)
        if total_defs >= 10:
            breakdown["代码规模分"] = 10
        elif total_defs >= 5:
            breakdown["代码规模分"] = 7
        elif total_defs >= 2:
            breakdown["代码规模分"] = 5
        else:
            breakdown["代码规模分"] = 2
        
        # ===== 2. 复杂度评分 (0-15分) - 实现质量指标 =====
        if 3 <= complexity <= 6:
            breakdown["复杂度分"] = 15  # 中等复杂度最优
        elif complexity > 6:
            breakdown["复杂度分"] = 10  # 高复杂度
        elif complexity > 1:
            breakdown["复杂度分"] = 8   # 低复杂度
        else:
            breakdown["复杂度分"] = 3
        
        # ===== 3. 自定义实现评分 (0-15分) =====
        if custom_impl >= 15:
            breakdown["自定义实现分"] = 15
        elif custom_impl >= 10:
            breakdown["自定义实现分"] = 12
        elif custom_impl >= 5:
            breakdown["自定义实现分"] = 8
        elif custom_impl >= 2:
            breakdown["自定义实现分"] = 5
        else:
            breakdown["自定义实现分"] = 2
        
        # ===== 4. 算法创新性评分 (0-20分) - 核心创新指标 =====
        algorithm_innovation = 0
        innovation_reasons = []
        
        # 检测自定义数据结构
        if re.search(r'class\s+\w*(Tree|Graph|Queue|Stack|Heap|Cache|Buffer)', code):
            algorithm_innovation += 5
            innovation_reasons.append("自定义数据结构")
        
        # 检测算法实现特征
        algo_patterns = [
            (r'def\s+\w*(sort|search|traverse|optimize|compute|calculate|parse|transform)', "自定义算法函数"),
            (r'(递归|recursion|dynamic\s*programming|dp\[)', "递归/动态规划"),
            (r'(bfs|dfs|dijkstra|backtrack)', "图算法/回溯"),
            (r'(embedding|vector|similarity|distance)', "向量/相似度计算"),
            (r'(tokenize|parse|compile|interpret)', "解析/编译逻辑"),
            (r'(agent|orchestrat|pipeline|workflow)', "智能体/流程编排"),
        ]
        
        for pattern, reason in algo_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                algorithm_innovation += 3
                innovation_reasons.append(reason)
        
        algorithm_innovation = min(20, algorithm_innovation)
        breakdown["算法创新分"] = algorithm_innovation
        
        # ===== 5. 异步编程加分 (0-5分) =====
        if counts.get("async_functions", 0) > 0:
            breakdown["异步编程加分"] = 5
        
        # ===== 6. 设计模式加分 (0-5分) =====
        design_patterns = [
            (r'class\s+\w*Factory', "工厂模式"),
            (r'class\s+\w*Singleton|_instance\s*=', "单例模式"),
            (r'class\s+\w*Observer|on_\w+|emit|subscribe', "观察者模式"),
            (r'class\s+\w*Strategy|execute\s*\(', "策略模式"),
            (r'__enter__|__exit__|with\s+', "上下文管理"),
        ]
        patterns_found = []
        for pattern, name in design_patterns:
            if re.search(pattern, code):
                patterns_found.append(name)
        if patterns_found:
            breakdown["设计模式加分"] = min(5, len(patterns_found) * 2)
        
        # ===== 计算总分 =====
        total_score = sum(breakdown.values())
        total_score = min(100, max(0, total_score))
        
        # ===== 区分算法创新 vs 实现质量 =====
        # 算法创新性 = 算法创新分 + 自定义实现分（权重0.5）
        algorithm_innovation_score = breakdown["算法创新分"] + breakdown["自定义实现分"] * 0.5
        
        # 实现质量 = 复杂度分 + 代码规模分 + 异步编程分 + 设计模式分
        implementation_quality_score = (
            breakdown["复杂度分"] + 
            breakdown["代码规模分"] + 
            breakdown["异步编程加分"] + 
            breakdown["设计模式加分"]
        )
        
        # ===== 生成新颖性解释 =====
        novelty_explanation = self._generate_novelty_explanation(
            novelty, innovation_reasons, patterns_found, custom_impl
        )
        
        return {
            "total_score": total_score,
            "breakdown": breakdown,
            "algorithm_innovation_score": algorithm_innovation_score,
            "implementation_quality_score": implementation_quality_score,
            "novelty_explanation": novelty_explanation,
            "innovation_reasons": innovation_reasons,
            "design_patterns": patterns_found,
        }
    
    def _generate_novelty_explanation(self, novelty: float, innovation_reasons: List[str],
                                      design_patterns: List[str], custom_impl: int) -> str:
        """
        生成新颖性评分的详细解释
        
        Args:
            novelty: 新颖性基础分
            innovation_reasons: 创新点列表
            design_patterns: 设计模式列表
            custom_impl: 自定义实现数
            
        Returns:
            解释文本
        """
        parts = []
        
        # 基础新颖性说明
        if novelty >= 0.7:
            parts.append(f"代码新颖性基础评分{novelty:.0%}（高）")
        elif novelty >= 0.4:
            parts.append(f"代码新颖性基础评分{novelty:.0%}（中）")
        else:
            parts.append(f"代码新颖性基础评分{novelty:.0%}（低）")
        
        # 创新点说明
        if innovation_reasons:
            parts.append(f"检测到创新特征: {', '.join(innovation_reasons[:3])}")
        else:
            parts.append("未检测到明显的算法创新特征")
        
        # 设计模式说明
        if design_patterns:
            parts.append(f"使用设计模式: {', '.join(design_patterns)}")
        
        # 自定义实现说明
        if custom_impl >= 10:
            parts.append(f"自定义实现丰富({custom_impl}处复杂逻辑)")
        elif custom_impl >= 5:
            parts.append(f"有一定自定义实现({custom_impl}处)")
        else:
            parts.append(f"自定义实现较少({custom_impl}处)，可能以API封装为主")
        
        return "；".join(parts)
    
    def _analyze_typescript_javascript(self, code: str) -> Dict[str, Any]:
        """
        分析TypeScript/JavaScript代码（基于正则）
        
        Args:
            code: TS/JS代码
            
        Returns:
            分析结果字典
        """
        # 统计函数
        func_patterns = [
            r'function\s+\w+',  # function foo()
            r'const\s+\w+\s*=\s*(?:async\s+)?\(',  # const foo = () =>
            r'(?:async\s+)?function\s*\(',  # async function()
            r'\w+\s*:\s*(?:async\s+)?\(',  # method: () =>
        ]
        func_count = sum(len(re.findall(p, code)) for p in func_patterns)
        
        # 统计类/接口
        class_count = len(re.findall(r'(?:class|interface|type)\s+\w+', code))
        
        # 统计异步函数
        async_count = len(re.findall(r'async\s+(?:function|\()', code))
        
        # 检测React组件
        react_components = len(re.findall(r'(?:export\s+)?(?:const|function)\s+\w+.*?(?:React\.FC|JSX\.Element|\<\w+)', code))
        
        # 检测Hook使用
        hooks = re.findall(r'use[A-Z]\w+', code)
        
        # 检测API调用
        api_calls = len(re.findall(r'(?:fetch|axios|api)\s*\(', code, re.IGNORECASE))
        
        # 复杂度指标
        loops = len(re.findall(r'(?:for|while|\.map|\.forEach|\.reduce)\s*\(', code))
        conditionals = len(re.findall(r'(?:if|switch|\?|&&|\|\|)', code))
        
        # 特征提取
        features = []
        if async_count > 0:
            features.append(f"异步函数 ({async_count}个)")
        if react_components > 0:
            features.append(f"React组件 ({react_components}个)")
        if hooks:
            unique_hooks = list(set(hooks))[:3]
            features.append(f"Hooks: {', '.join(unique_hooks)}")
        if "TypeScript" in code or ": " in code:
            features.append("TypeScript类型定义")
        
        return {
            "functions": func_count,
            "classes": class_count,
            "async_functions": async_count,
            "loops": loops,
            "conditionals": conditionals,
            "features": features[:5],
        }
    
    def _is_python_code(self, code: str) -> bool:
        """判断是否为Python代码"""
        python_indicators = ["def ", "class ", "import ", "from ", "self.", "elif "]
        js_indicators = ["const ", "let ", "function ", "=>", "export ", "import {"]
        
        py_score = sum(1 for ind in python_indicators if ind in code)
        js_score = sum(1 for ind in js_indicators if ind in code)
        
        return py_score > js_score
    
    def analyze(self, code_files: Dict[str, str], baseline_codes: List[str] = None) -> CodeAnalysisResult:
        """
        分析代码创新性（支持Python/TypeScript/JavaScript）
        
        Args:
            code_files: 代码文件 {路径: 内容}
            baseline_codes: 基线代码列表（用于相似度对比）
            
        Returns:
            CodeAnalysisResult分析结果
        """
        if not code_files:
            return CodeAnalysisResult(
                score=30.0,
                total_functions=0,
                total_classes=0,
                custom_implementations=0,
                avg_complexity=0.0,
                novelty_score=0.5,
                key_features=[],
                details="未检测到代码文件",
                scoring_breakdown={"基础分": 30.0},
                algorithm_innovation_score=0.0,
                implementation_quality_score=0.0,
                novelty_explanation="未检测到代码文件，无法评估新颖性",
            )
        
        # 合并所有代码
        all_code = "\n\n".join(code_files.values())
        
        # 判断代码类型
        is_python = self._is_python_code(all_code)
        
        if is_python:
            # Python代码：使用AST分析
            tree = self._parse_ast(all_code)
            if tree is None:
                # AST解析失败，使用正则分析
                func_count = len(re.findall(r'def\s+\w+', all_code))
                class_count = len(re.findall(r'class\s+\w+', all_code))
                custom_impl = self._detect_custom_implementations(all_code)
                
                # 使用新的评分方法
                counts = {"functions": func_count, "async_functions": 0, "classes": class_count}
                score_result = self._calculate_score(counts, 0.0, custom_impl, 0.5, all_code)
                
                return CodeAnalysisResult(
                    score=score_result['total_score'],
                    total_functions=func_count,
                    total_classes=class_count,
                    custom_implementations=custom_impl,
                    avg_complexity=0.0,
                    novelty_score=0.5,
                    key_features=["Python代码正则分析"],
                    details=f"函数: {func_count}, 类: {class_count}",
                    scoring_breakdown=score_result['breakdown'],
                    algorithm_innovation_score=score_result['algorithm_innovation_score'],
                    implementation_quality_score=score_result['implementation_quality_score'],
                    novelty_explanation=score_result['novelty_explanation'],
                )
            
            # 统计元素
            counts = self._count_elements(tree)
            complexity = self._calculate_complexity(all_code, tree)
            custom_impl = self._detect_custom_implementations(all_code)
            key_features = self._extract_key_features(all_code, tree)
        else:
            # TypeScript/JavaScript代码：使用正则分析
            ts_result = self._analyze_typescript_javascript(all_code)
            counts = {
                "functions": ts_result["functions"],
                "async_functions": ts_result["async_functions"],
                "classes": ts_result["classes"],
                "loops": ts_result["loops"],
                "conditionals": ts_result["conditionals"],
            }
            complexity = (ts_result["loops"] + ts_result["conditionals"]) / max(ts_result["functions"], 1)
            custom_impl = ts_result["functions"] + ts_result["classes"]
            key_features = ts_result["features"]
        
        # 计算新颖性
        novelty_score = 0.5
        if self.similarity_calculator and baseline_codes:
            novelty_score = self.similarity_calculator.compute_novelty_score(all_code, baseline_codes)
        
        # 计算综合得分（使用新的详细评分方法）
        score_result = self._calculate_score(counts, complexity, custom_impl, novelty_score, all_code)
        
        # 生成详细说明
        total_funcs = counts.get("functions", 0) + counts.get("async_functions", 0)
        details = f"函数: {total_funcs}, 类: {counts.get('classes', 0)}, 复杂度: {complexity:.1f}, 算法创新: {score_result['algorithm_innovation_score']:.0f}分"
        
        return CodeAnalysisResult(
            score=score_result['total_score'],
            total_functions=total_funcs,
            total_classes=counts.get("classes", 0),
            custom_implementations=custom_impl,
            avg_complexity=complexity,
            novelty_score=novelty_score,
            key_features=key_features,
            details=details,
            # 新增透明度字段
            scoring_breakdown=score_result['breakdown'],
            algorithm_innovation_score=score_result['algorithm_innovation_score'],
            implementation_quality_score=score_result['implementation_quality_score'],
            novelty_explanation=score_result['novelty_explanation'],
        )


# 测试代码
if __name__ == "__main__":
    analyzer = CodeAnalyzer()
    
    test_code = {
        "main.py": """
import asyncio
from typing import List

class CustomAgent:
    def __init__(self, name: str):
        self.name = name
        self._cache = {}
    
    async def process(self, query: str) -> str:
        if query in self._cache:
            return self._cache[query]
        
        result = await self._compute(query)
        self._cache[query] = result
        return result
    
    async def _compute(self, query: str) -> str:
        # 复杂计算逻辑
        for i in range(10):
            if i % 2 == 0:
                continue
            query = f"{query}_{i}"
        return query
    
    def __repr__(self):
        return f"CustomAgent({self.name})"

def create_agent(name: str) -> CustomAgent:
    return CustomAgent(name)
""",
    }
    
    result = analyzer.analyze(test_code)
    print(f"得分: {result.score:.1f}")
    print(f"函数数: {result.total_functions}")
    print(f"类数: {result.total_classes}")
    print(f"关键特征: {result.key_features}")
    print(f"详情: {result.details}")
