"""简单核心功能测试脚本

直接测试创新性评估的核心功能，不依赖Web界面。
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=== 简单核心功能测试 ===")
print(f"Python版本: {sys.version}")

try:
    # 测试1: 导入核心模块
    print("\n1. 测试核心模块导入...")
    from core.innovation_scorer import InnovationScorer
    from core.report_quality import ReportQualityEvaluator
    from config import DEFAULT_WEIGHTS
    print("✓ 核心模块导入成功!")
    
    # 测试2: 初始化评分器
    print("\n2. 测试评分器初始化...")
    scorer = InnovationScorer(use_modelscope=False, use_deepseek=False)
    print("✓ 评分器初始化成功!")
    
    # 测试3: 初始化质量评估器
    print("\n3. 测试质量评估器初始化...")
    quality_evaluator = ReportQualityEvaluator()
    print("✓ 质量评估器初始化成功!")
    
    # 测试4: 生成测试报告
    print("\n4. 测试报告生成...")
    # 创建一个简单的测试报告
    test_report = """
# AI应用创新性评估报告

**项目**: [test-project](https://github.com/test/test-project)
**语言**: Python | **Stars**: 100

---

## 开篇总览
这是一个测试项目，用于验证报告质量评估功能。

## 创新性总评

### 总体评分：75.0/100 ⭐⭐⭐⭐

**创新等级**：显著创新
**定性评价**：技术与场景兼备的综合型创新

## 详细维度分析
### 技术选型与实现
**得分**：60/100
使用了标准的Python技术栈。

### 场景创新性
**得分**：80/100
应用场景新颖，服务特定用户群体。

## 具体改进建议
### 技术加固
- 建议1：引入前沿AI框架

## 评委关注点
- 问题1：与同类产品的差异化？
"""
    
    # 测试质量评估
    print("\n5. 测试报告质量评估...")
    quality_result = quality_evaluator.evaluate(test_report)
    print(f"✓ 质量评估成功，得分: {quality_result.overall_score:.1f}/100")
    print(f"  评估结果: {'合格' if quality_result.is_qualified else '不合格'}")
    
    print("\n=== 测试完成 ===")
    print("核心功能测试通过！系统已准备就绪。")
    print("\n你可以：")
    print("1. 使用核心API进行评估")
    print("2. 检查技术文档了解系统架构")
    print("3. 参考测试协议进行完整测试")

except Exception as e:
    print(f"\n=== 测试失败 ===")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n请检查上述错误信息并解决问题后重试。")
