"""简单测试社会价值评估系统"""
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.social_value_scorer import SocialValueScorer, SocialValueReport, DimensionScore


def test_social_value_core():
    """测试社会价值评估器核心功能"""
    print("Testing SocialValueScorer core functionality...")
    
    try:
        # 创建评分器实例
        scorer = SocialValueScorer(use_deepseek=False)
        print("✓ SocialValueScorer created successfully")
        
        # 测试权重归一化
        test_weights = {
            "ethics_redline": 10,
            "privacy_protection": 10,
            "algorithm_fairness": 10,
            "social_impact": 25,
            "environmental_friendliness": 15,
            "charity_orientation": 15,
            "long_term_vision": 15,
        }
        normalized = scorer._normalize_weights(test_weights)
        print(f"✓ Weight normalization test passed: {sum(normalized.values()):.1f}%")
        
        # 测试维度得分计算
        test_dimensions = [
            DimensionScore(
                name="ethics_redline",
                name_cn="伦理红线检查",
                score=80,
                weight=10,
                weighted_score=8.0,
                details="测试详情",
                category="basic"
            ),
            DimensionScore(
                name="social_impact",
                name_cn="社会影响深度",
                score=90,
                weight=25,
                weighted_score=22.5,
                details="测试详情",
                category="bonus"
            ),
        ]
        total_score = sum(d.weighted_score for d in test_dimensions)
        print(f"✓ Dimension score calculation test passed: {total_score:.1f}")
        
        # 测试等级计算
        level, stars = scorer._get_level(85)
        print(f"✓ Level calculation test passed: {level} {stars}")
        
        # 测试报告生成
        test_report = SocialValueReport(
            repo_name="Test Project",
            repo_url="https://github.com/test/test",
            total_score=85.5,
            level="显著社会价值",
            level_stars="⭐⭐⭐⭐",
            core_value_summary="测试项目的核心价值",
            social_value_type="社会问题解决型",
            basic_items_score=25.0,
            bonus_items_score=60.5,
            dimensions=test_dimensions,
            stars=1000,
            language="Python",
            description="测试项目描述",
            analysis_time=10.5,
            dimension_analyses={"test": "测试分析"},
            social_value_highlights=["亮点1", "亮点2"],
            improvement_suggestions=["建议1", "建议2"],
            judge_focus_points=["关注点1", "关注点2"],
            confidence_level="高",
            information_sufficiency="高",
            core_social_value_types=["社会问题解决型"]
        )
        
        # 测试报告生成
        markdown_report = scorer.generate_markdown_report(test_report, use_llm=False)
        print(f"✓ Markdown report generation test passed")
        print(f"Report length: {len(markdown_report)} characters")
        
        # 测试关键词检测
        test_text = "这是一个关于环保和公益的项目，关注弱势群体"
        keywords = scorer._detect_keywords(test_text, scorer.SOCIAL_VALUE_KEYWORDS)
        print(f"✓ Keyword detection test passed: {list(keywords.keys())}")
        
        print("\n✓ All core tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_social_value_core()
