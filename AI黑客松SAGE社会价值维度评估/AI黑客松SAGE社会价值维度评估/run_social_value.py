"""直接运行社会价值评估"""
import sys
import traceback

print("AI黑客松社会价值评估系统")
print("=" * 50)

# 测试仓库URL
test_urls = [
    "https://github.com/microsoft/autogen",  # 微软的多智能体系统
    "https://github.com/langchain-ai/langchain",  # LangChain框架
    "https://github.com/openai/openai-python",  # OpenAI Python SDK
]

print("可用的测试仓库:")
for i, url in enumerate(test_urls, 1):
    print(f"{i}. {url}")

# 自动选择测试URL（选择第二个仓库：LangChain）
index = 1  # 选择第二个仓库
if 0 <= index < len(test_urls):
    target_url = test_urls[index]
    print(f"\n正在评估: {target_url}")
else:
    print("无效选择，使用默认仓库")
    target_url = test_urls[0]

print("\n开始评估...")

# 导入并运行评估
try:
    # 导入社会价值评估器
    from core.social_value_scorer import SocialValueScorer
    
    # 创建评估器实例
    scorer = SocialValueScorer(use_deepseek=False)
    print("✓ 评估器初始化成功")
    
    # 定义进度回调
    def progress_callback(prog, message):
        print(f"[{prog:.1f}] {message}")
    
    # 执行评估
    report = scorer.analyze(target_url, progress_callback=progress_callback)
    
    # 打印评估结果
    print("\n评估结果:")
    print("=" * 50)
    print(f"仓库名称: {report.repo_name}")
    print(f"总分: {report.total_score:.1f}/100")
    print(f"等级: {report.level} {report.level_stars}")
    print(f"核心价值: {report.core_value_summary}")
    print(f"社会价值类型: {', '.join(report.core_social_value_types)}")
    
    # 生成报告
    print("\n生成详细报告...")
    markdown_report = scorer.generate_markdown_report(report, use_llm=False)
    
    # 保存报告到文件
    report_file = f"social_value_report_{report.repo_name}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print(f"\n✓ 评估完成!")
    print(f"详细报告已保存到: {report_file}")
    
    # 显示报告预览
    print("\n报告预览:")
    print("=" * 50)
    preview_lines = markdown_report.split('\n')[:30]
    print('\n'.join(preview_lines))
    print("...")

except Exception as e:
    print(f"\n✗ 评估失败: {e}")
    print("详细错误:")
    traceback.print_exc()

print("\n" + "=" * 50)
print("评估完成!")
input("按Enter键退出...")
