"""核心功能测试脚本

直接测试AI评估报告系统的核心功能，验证改进效果。
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.innovation_scorer import InnovationScorer
from config import DEFAULT_WEIGHTS


def test_innovation_scorer():
    """测试创新评分器核心功能"""
    print("=== 测试创新评分器核心功能 ===")
    
    try:
        # 初始化评分器
        scorer = InnovationScorer(use_modelscope=False, use_deepseek=False)
        print("✓ 创新评分器初始化成功")
        
        # 测试仓库URL
        test_repos = [
            "https://github.com/langchain-ai/langchain",
            "https://github.com/openai/openai-python",
            "https://github.com/microsoft/autogen",
        ]
        
        for repo_url in test_repos:
            print(f"\n=== 测试仓库: {repo_url} ===")
            
            try:
                # 执行分析
                report = scorer.analyze(repo_url, weights=DEFAULT_WEIGHTS)
                print(f"✓ 仓库分析成功: {report.repo_name}")
                print(f"  总分: {report.total_score:.1f}/100")
                print(f"  等级: {report.level} {report.level_stars}")
                print(f"  核心价值: {report.core_value_summary}")
                
                # 测试详细改进建议
                print("\n--- 测试详细改进建议 ---")
                if report.tech_suggestions:
                    print(f"✓ 技术加固建议: {len(report.tech_suggestions)} 条")
                    for i, suggestion in enumerate(report.tech_suggestions[:1], 1):
                        if isinstance(suggestion, dict):
                            print(f"  建议{i}: {suggestion.get('title')}")
                            print(f"  优先级: {suggestion.get('priority')}")
                            print(f"  描述: {suggestion.get('description')}")
                
                if report.scenario_suggestions:
                    print(f"✓ 场景深化建议: {len(report.scenario_suggestions)} 条")
                
                if report.product_suggestions:
                    print(f"✓ 产品化推进建议: {len(report.product_suggestions)} 条")
                
                # 测试评委问题生成
                print("\n--- 测试评委问题生成 ---")
                if report.judge_focus_points:
                    print(f"✓ 评委问题: {len(report.judge_focus_points)} 个")
                    for i, question in enumerate(report.judge_focus_points[:1], 1):
                        if isinstance(question, dict):
                            print(f"  问题{i}: {question.get('question')}")
                            print(f"  追问目的: {question.get('purpose')}")
                
                # 测试报告生成
                print("\n--- 测试报告生成 ---")
                markdown_report = scorer.generate_markdown_report(report, use_llm=False)
                print(f"✓ 报告生成成功，长度: {len(markdown_report)} 字符")
                
                # 检查报告质量评估
                if "报告质量评估结果" in markdown_report:
                    print("✓ 报告质量评估集成成功")
                
                # 保存测试报告
                report_file = f"test_report_{report.repo_name.replace('/', '_')}.md"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_report)
                print(f"✓ 测试报告保存: {report_file}")
                
            except Exception as e:
                print(f"✗ 测试失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n=== 核心功能测试完成 ===")
        
    except Exception as e:
        print(f"✗ 评分器初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_quality_evaluator():
    """测试报告质量评估器"""
    print("\n=== 测试报告质量评估器 ===")
    
    try:
        from core.report_quality import ReportQualityEvaluator
        
        evaluator = ReportQualityEvaluator()
        print("✓ 质量评估器初始化成功")
        
        # 测试质量评估
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

| 板块 | 得分 | 满分 | 占比 |
|------|------|------|------|
| 技术创新力 | 28.0 | 40 | 40% |
| 场景创新力 | 47.0 | 60 | 60% |

---

## 六维能力雷达图

*以下展示项目在6个关键维度的表现（满分100）：*

### 技术创新力 (40%)
- **技术选型与实现**: `██████░░░░` 60分
- **系统架构与设计**: `███████░░░` 70分
- **工程化与可持续性**: `██████░░░░` 60分

### 场景创新力 (60%)
- **问题定义与价值**: `███████░░░` 70分
- **场景创新性**: `████████░░` 80分
- **市场与生态契合度**: `██████░░░░` 60分

### 雷达图解读
优势维度：场景创新性(80分)、系统架构与设计(70分)
待提升维度：技术选型与实现(60分)、工程化与可持续性(60分)

---

## 详细维度分析

### 1. 技术选型与实现
**得分**：60/100（权重13%）
使用了标准的Python技术栈，实现了基本功能。建议引入更多前沿AI框架提升技术创新性。

### 2. 系统架构与设计
**得分**：70/100（权重13%）
采用模块化架构，代码组织清晰，易于维护和扩展。

### 3. 工程化与可持续性
**得分**：60/100（权重14%）
具备基本的工程化配置，但缺乏完整的测试覆盖和CI/CD流程。

### 4. 问题定义与价值
**得分**：70/100（权重18%）
问题定义清晰，目标用户明确，价值主张合理。

### 5. 场景创新性
**得分**：80/100（权重24%）
应用场景新颖，服务特定用户群体，具有一定的社会价值。

### 6. 市场与生态契合度
**得分**：60/100（权重18%）
与市场趋势有一定契合度，但生态集成能力有待提升。

---

## 具体改进建议

### 技术加固

#### 建议1：引入前沿AI框架（优先级：高）
**描述**：引入LangChain、AutoGen等前沿AI框架，提升技术创新性
**原因**：当前技术栈较为基础，缺乏前沿AI技术应用
**具体措施**：
1. 集成LangChain框架实现复杂的AI工作流
2. 引入AutoGen实现多智能体协作
3. 探索RAG技术提升系统性能
**预期效果**：显著提升技术创新性评分，增强系统功能复杂度

### 场景深化

#### 建议1：明确目标用户群体（优先级：高）
**描述**：深入理解特定用户群体的真实需求和使用场景
**原因**：目标用户不明确，场景创新性缺乏针对性
**具体措施**：
1. 进行用户调研和访谈
2. 创建详细的用户画像
3. 分析目标用户的具体痛点
**预期效果**：显著提升场景创新性评分，增强项目的针对性

### 产品化推进

#### 建议1：创建在线演示（优先级：高）
**描述**：创建在线Demo或演示视频，让评委快速体验核心功能
**原因**：缺乏直观的产品展示，评委难以理解项目价值
**具体措施**：
1. 部署在线Demo环境
2. 制作简短的功能演示视频
3. 提供详细的使用说明
**预期效果**：提升评委对项目的理解，展示产品价值

---

## 评委关注点

### 问题1：与市场上同类产品相比，本项目的核心差异化竞争力是什么？
**追问目的**：评估项目的市场定位和竞争优势
**期望回答**：希望团队能清晰阐述与竞品的具体差异点，以及这些差异如何形成竞争优势
**评分参考**：优秀：有明确的差异化优势和市场定位；良好：有一定差异化但不够突出；一般：差异化不明显；差：缺乏差异化认知

### 问题2：请详细说明项目的系统架构设计，以及这种设计如何支持产品的创新性和可扩展性？
**追问目的**：评估项目的架构设计能力和技术远见
**期望回答**：希望团队能清晰阐述系统架构的设计思路、关键组件、以及如何支持产品功能和未来扩展
**评分参考**：优秀：架构设计清晰合理且有技术远见；良好：架构基本合理；一般：架构设计简单；差：架构混乱缺乏规划

### 问题3：项目的应用场景创新性体现在哪些方面？与传统解决方案相比有哪些显著优势？
**追问目的**：评估项目的场景创新性和问题解决能力
**期望回答**：希望团队能详细说明场景创新点，以及如何通过技术手段解决传统方案的不足
**评分参考**：优秀：场景创新显著且有具体价值；良好：有一定场景创新；一般：场景创新不足；差：缺乏场景创新

---

*报告生成时间: 10.5秒 | SAGE AI创新性评估系统 v3.0（人性化版本）*

# 报告质量评估结果

## 总体评估

**总体得分**: 85.0/100
**评估结果**: 合格

## 各项指标得分

| 指标 | 得分 | 权重 | 加权得分 | 说明 |
|------|------|------|----------|------|
| 报告完整性 | 90.0 | 0.25 | 22.5 | 章节数: 8/8, 必要章节: 6/6 |
| 分析深度 | 80.0 | 0.30 | 24.0 | 总字数: 1500/2000, 简短维度: 1/6 |
| 专业性 | 90.0 | 0.20 | 18.0 | 专业元素: 5/5, 专业术语: 8/8 |
| 表达清晰度 | 85.0 | 0.15 | 12.8 | 结构元素: 45, 平均句子长度: 12.5, 格式问题: 0 |
| 结构合理性 | 85.0 | 0.10 | 8.5 | 章节数: 8, 流程问题: 0 |

## 改进建议

1. 增加报告长度，建议至少2000字
2. 增加技术选型与实现维度的分析深度

## 质量标准参考

| 得分范围 | 评价 |
|---------|------|
| 90-100 | 优秀 |
| 80-89 | 良好 |
| 70-79 | 合格 |
| 60-69 | 基本合格 |
| <60 | 不合格 |
"""
        
        quality_result = evaluator.evaluate(test_report)
        print(f"✓ 质量评估成功，得分: {quality_result.overall_score:.1f}/100")
        print(f"  评估结果: {'合格' if quality_result.is_qualified else '不合格'}")
        
        # 生成质量评估报告
        quality_report = evaluator.generate_quality_report(quality_result)
        print(f"✓ 质量评估报告生成成功")
        
        # 保存质量评估报告
        with open('test_quality_report.md', 'w', encoding='utf-8') as f:
            f.write(quality_report)
        print(f"✓ 质量评估报告保存: test_quality_report.md")
        
    except Exception as e:
        print(f"✗ 质量评估器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("开始核心功能测试...")
    test_innovation_scorer()
    test_quality_evaluator()
    print("\n核心功能测试完成！")
