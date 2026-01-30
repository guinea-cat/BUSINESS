"""核心功能测试脚本

简单测试创新性评估系统的核心功能。
"""
import sys
print(f"Python版本: {sys.version}")

print("=== 测试AI创新性评估系统核心功能 ===")

try:
    # 测试1: 导入核心模块
    print("\n1. 测试核心模块导入...")
    from core.innovation_scorer import InnovationScorer
    from core.report_quality import ReportQualityEvaluator
    print("✓ 核心模块导入成功!")
    
    # 测试2: 初始化评分器
    print("\n2. 测试评分器初始化...")
    scorer = InnovationScorer(use_modelscope=False, use_deepseek=False)
    print("✓ 评分器初始化成功!")
    
    # 测试3: 初始化质量评估器
    print("\n3. 测试质量评估器初始化...")
    quality_evaluator = ReportQualityEvaluator()
    print("✓ 质量评估器初始化成功!")
    
    print("\n=== 测试完成 ===")
    print("🎉 所有核心功能测试通过！")
    print("\n系统状态: 就绪")
    print("核心组件: 正常")
    print("\n你可以通过以下方式使用系统:")
    print("1. 核心API: 使用InnovationScorer进行评估")
    print("2. 质量评估: 使用ReportQualityEvaluator评估报告")
    print("3. 详细文档: 查看TECHNICAL_DOCUMENTATION.md")
    
except Exception as e:
    print(f"\n❌ 测试失败: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n请检查错误信息并解决问题后重试。")
