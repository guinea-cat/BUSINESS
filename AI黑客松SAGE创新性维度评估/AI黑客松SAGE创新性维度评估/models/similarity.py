"""魔搭API相似度计算模块

功能：
- 封装魔搭multi-modal-similarity模型调用
- 代码文本语义嵌入
- 余弦相似度计算
- 基线代码对比与风险检测
- 降级方案：简单文本相似度
"""
import os
import hashlib
import re
from typing import List, Optional, Union, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

import numpy as np

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import MODELSCOPE_API_TOKEN, SIMILARITY_THRESHOLD

# 设置魔搭Token
os.environ["MODELSCOPE_API_TOKEN"] = MODELSCOPE_API_TOKEN


@dataclass
class SimilarityRisk:
    """相似度风险结果"""
    source_repo: str  # 来源仓库
    source_file: str  # 来源文件
    target_file: str  # 目标文件
    similarity: float  # 相似度
    risk_level: str  # 风险等级: high/medium/low
    matched_features: List[str]  # 匹配的特征
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": f"{self.source_repo}/{self.source_file}" if self.source_repo else self.source_file,
            "target_file": self.target_file,
            "similarity": round(self.similarity, 3),
            "level": self.risk_level,
            "matched_features": self.matched_features[:5],
        }


class SimilarityCalculator:
    """相似度计算器"""
    
    def __init__(self, use_modelscope: bool = True):
        """
        初始化相似度计算器
        
        Args:
            use_modelscope: 是否使用魔搭API，False则使用简单文本相似度
        """
        self.use_modelscope = use_modelscope
        self.pipeline = None
        self._init_model()
    
    def _init_model(self):
        """初始化模型"""
        if not self.use_modelscope:
            return
        
        try:
            from modelscope.pipelines import pipeline
            from modelscope.utils.constant import Tasks
            
            # 使用多模态相似度模型
            # 注：该模型主要用于图文相似度，对于纯文本也有效果
            self.pipeline = pipeline(
                Tasks.multi_modal_similarity,
                model='iic/multi-modal_team-vit-large-patch14_multi-modal-similarity'
            )
            print("魔搭API模型加载成功")
        except Exception as e:
            print(f"魔搭API模型加载失败，将使用简单文本相似度: {e}")
            self.use_modelscope = False
            self.pipeline = None
    
    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """
        简单文本相似度（基于词汇重叠）
        
        使用Jaccard相似度作为降级方案
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数 [0, 1]
        """
        # 分词（简单按空格和标点分割）
        import re
        
        def tokenize(text: str) -> set:
            # 转小写，提取字母数字词
            words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
            return set(words)
        
        set1 = tokenize(text1)
        set2 = tokenize(text2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _code_structure_similarity(self, code1: str, code2: str) -> float:
        """
        代码结构相似度
        
        基于代码特征（函数名、类名、导入等）计算相似度
        
        Args:
            code1: 代码1
            code2: 代码2
            
        Returns:
            相似度分数 [0, 1]
        """
        import re
        
        def extract_features(code: str) -> set:
            features = set()
            
            # 提取import
            imports = re.findall(r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)', code)
            features.update(f"import:{imp}" for imp in imports)
            
            # 提取函数定义
            functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
            features.update(f"func:{func}" for func in functions)
            
            # 提取类定义
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
            features.update(f"class:{cls}" for cls in classes)
            
            # 提取变量赋值
            variables = re.findall(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=', code, re.MULTILINE)
            features.update(f"var:{var}" for var in variables[:20])  # 限制数量
            
            return features
        
        features1 = extract_features(code1)
        features2 = extract_features(code2)
        
        if not features1 or not features2:
            return 0.0
        
        intersection = len(features1 & features2)
        union = len(features1 | features2)
        
        return intersection / union if union > 0 else 0.0
    
    def compute_similarity(self, text1: str, text2: str, is_code: bool = False) -> float:
        """
        计算两段文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            is_code: 是否为代码文本
            
        Returns:
            相似度分数 [0, 1]
        """
        if not text1 or not text2:
            return 0.0
        
        # 截断过长文本
        max_len = 2000
        text1 = text1[:max_len]
        text2 = text2[:max_len]
        
        # 尝试使用魔搭API
        if self.pipeline is not None:
            try:
                # 魔搭多模态相似度模型的输入格式
                # 注意：这个模型主要用于图文匹配，对纯文本效果可能有限
                # 这里我们将文本作为输入
                result = self.pipeline({
                    'text': text1,
                    'text2': text2,
                })
                if isinstance(result, dict) and 'score' in result:
                    return float(result['score'])
                elif isinstance(result, (int, float)):
                    return float(result)
            except Exception as e:
                print(f"魔搭API调用失败: {e}")
        
        # 降级方案：使用简单相似度
        if is_code:
            # 对于代码，结合词汇和结构相似度
            text_sim = self._simple_text_similarity(text1, text2)
            struct_sim = self._code_structure_similarity(text1, text2)
            return 0.4 * text_sim + 0.6 * struct_sim
        else:
            return self._simple_text_similarity(text1, text2)
    
    def compute_batch_similarity(self, query: str, candidates: List[str], is_code: bool = False) -> List[float]:
        """
        批量计算相似度
        
        Args:
            query: 查询文本
            candidates: 候选文本列表
            is_code: 是否为代码文本
            
        Returns:
            相似度分数列表
        """
        return [self.compute_similarity(query, candidate, is_code) for candidate in candidates]
    
    def compute_novelty_score(self, target_code: str, baseline_codes: List[str]) -> float:
        """
        计算新颖性分数
        
        与基线代码对比，计算目标代码的新颖程度
        新颖性 = 1 - 最高相似度
        
        Args:
            target_code: 目标代码
            baseline_codes: 基线代码列表
            
        Returns:
            新颖性分数 [0, 1]，越高越新颖
        """
        if not baseline_codes:
            return 1.0  # 无基线对比，默认最高新颖性
        
        similarities = self.compute_batch_similarity(target_code, baseline_codes, is_code=True)
        max_similarity = max(similarities) if similarities else 0.0
        
        # 新颖性 = 1 - 最高相似度
        return 1.0 - max_similarity
    
    def get_text_hash(self, text: str) -> str:
        """获取文本的哈希值（用于缓存）"""
        return hashlib.md5(text.encode()).hexdigest()[:16]
    
    def _get_risk_level(self, similarity: float) -> str:
        """根据相似度返回风险等级"""
        if similarity >= SIMILARITY_THRESHOLD.get("high_risk", 0.85):
            return "高"
        elif similarity >= SIMILARITY_THRESHOLD.get("medium_risk", 0.70):
            return "中"
        elif similarity >= SIMILARITY_THRESHOLD.get("low_risk", 0.50):
            return "低"
        return "无"
    
    def _extract_code_features(self, code: str) -> Dict[str, set]:
        """提取代码特征用于匹配分析"""
        features = {
            "imports": set(),
            "functions": set(),
            "classes": set(),
            "api_calls": set(),
        }
        
        # 提取import
        imports = re.findall(r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)', code)
        features["imports"] = set(imports)
        
        # 提取函数定义
        functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        features["functions"] = set(functions)
        
        # 提取类定义
        classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
        features["classes"] = set(classes)
        
        # 提取API调用模式
        api_calls = re.findall(r'\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', code)
        features["api_calls"] = set(api_calls)
        
        return features
    
    def detect_similarity_risks(self, 
                                target_files: Dict[str, str],
                                baseline_repos: List[Dict[str, Any]],
                                threshold: float = 0.5) -> List[SimilarityRisk]:
        """
        检测与基线代码库的相似度风险
        
        Args:
            target_files: 目标代码文件 {文件路径: 内容}
            baseline_repos: 基线仓库列表，每个包含 {name, code_files: {path: content}}
            threshold: 相似度阈值
            
        Returns:
            相似度风险列表
        """
        risks = []
        
        for target_path, target_code in target_files.items():
            if not target_code.strip():
                continue
            
            target_features = self._extract_code_features(target_code)
            
            for baseline in baseline_repos:
                repo_name = baseline.get("name", "unknown")
                baseline_files = baseline.get("code_files", {})
                
                for base_path, base_code in baseline_files.items():
                    if not base_code.strip():
                        continue
                    
                    # 计算相似度
                    similarity = self.compute_similarity(target_code, base_code, is_code=True)
                    
                    if similarity >= threshold:
                        # 找出匹配的特征
                        base_features = self._extract_code_features(base_code)
                        matched = []
                        
                        for feat_type in ["imports", "functions", "classes"]:
                            common = target_features[feat_type] & base_features[feat_type]
                            if common:
                                matched.extend([f"{feat_type}:{f}" for f in list(common)[:3]])
                        
                        risk = SimilarityRisk(
                            source_repo=repo_name,
                            source_file=base_path,
                            target_file=target_path,
                            similarity=similarity,
                            risk_level=self._get_risk_level(similarity),
                            matched_features=matched,
                        )
                        risks.append(risk)
        
        # 按相似度降序排序，只返回前10个
        risks.sort(key=lambda r: r.similarity, reverse=True)
        return risks[:10]
    
    def compute_overall_novelty(self, 
                                target_files: Dict[str, str],
                                baseline_repos: List[Dict[str, Any]]) -> Tuple[float, List[Dict]]:
        """
        计算整体新颖性分数和风险列表
        
        Args:
            target_files: 目标代码文件
            baseline_repos: 基线仓库列表
            
        Returns:
            (新颖性分数, 风险列表)
        """
        if not target_files or not baseline_repos:
            return 1.0, []
        
        # 检测风险
        risks = self.detect_similarity_risks(target_files, baseline_repos)
        
        if not risks:
            return 1.0, []
        
        # 计算平均新颖性（1 - 最高相似度）
        max_similarity = max(r.similarity for r in risks)
        novelty = 1.0 - max_similarity
        
        # 转换风险为字典格式
        risk_dicts = [r.to_dict() for r in risks if r.risk_level in ["高", "中"]]
        
        return novelty, risk_dicts


# 简化版相似度计算器（不依赖魔搭）
class SimpleSimilarityCalculator(SimilarityCalculator):
    """简化版相似度计算器，不使用魔搭API"""
    
    def __init__(self):
        super().__init__(use_modelscope=False)


# 测试代码
if __name__ == "__main__":
    # 测试简单相似度
    calc = SimpleSimilarityCalculator()
    
    code1 = """
import openai
from langchain import LLMChain

def get_response(prompt):
    client = openai.Client()
    return client.chat.completions.create(messages=[{"role": "user", "content": prompt}])
"""
    
    code2 = """
import openai

def ask_gpt(question):
    client = openai.OpenAI()
    response = client.chat.completions.create(messages=[{"role": "user", "content": question}])
    return response
"""
    
    code3 = """
import torch
from transformers import AutoModel

class CustomModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = AutoModel.from_pretrained("bert-base")
    
    def forward(self, x):
        return self.encoder(x)
"""
    
    print(f"代码1 vs 代码2 相似度: {calc.compute_similarity(code1, code2, is_code=True):.3f}")
    print(f"代码1 vs 代码3 相似度: {calc.compute_similarity(code1, code3, is_code=True):.3f}")
    print(f"代码1 新颖性分数 (基线: code2, code3): {calc.compute_novelty_score(code1, [code2, code3]):.3f}")
