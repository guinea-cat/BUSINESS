"""测试社会价值评估系统"""
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.social_value_scorer import SocialValueScorer


def test_social_value_scorer():
    """测试社会价值评估器"""
    print("Testing SocialValueScorer...")
    
    try:
        # 创建评分器实例
        scorer = SocialValueScorer(use_deepseek=False)
        print("✓ SocialValueScorer created successfully")
        
        # 测试评估功能
        test_url = "https://github.com/langchain-ai/langchain"
        print(f"\nTesting analysis for: {test_url}")
        
        def progress_callback(prog, message):
            print(f"Progress: {prog:.1f} - {message}")
        
        # 执行分析
        report = scorer.analyze(test_url, progress_callback=progress_callback)
        
        # 打印报告信息
        print(f"\nReport generated successfully!")
        print(f"Repository: {report.repo_name}")
        print(f"Total Score: {report.total_score:.1f}")
        print(f"Level: {report.level} {report.level_stars}")
        print(f"Core Value: {report.core_value_summary}")
        print(f"Social Value Types: {', '.join(report.core_social_value_types)}")
        
        # 测试报告生成
        markdown_report = scorer.generate_markdown_report(report, use_llm=False)
        print(f"\nMarkdown report generated (first 500 chars):")
        print(markdown_report[:500] + "...")
        
        print("\n✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_social_value_scorer()
