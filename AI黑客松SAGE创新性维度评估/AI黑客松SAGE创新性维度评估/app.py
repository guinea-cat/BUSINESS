"""AI应用创新性评估系统 - Gradio界面（人性化版本 v3.0）

功能：
- URL输入框
- 6维度权重配置（技术创新力40% + 场景创新力60%）
- 评估按钮+进度显示
- 人性化Markdown报告展示
"""
import gradio as gr
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_WEIGHTS
from core.innovation_scorer import InnovationScorer


# 全局评分器实例
scorer = None

def get_scorer(use_deepseek: bool = True):
    """获取评分器实例（每次都创建新实例以确保使用最新的提示词库）"""
    return InnovationScorer(use_modelscope=False, use_deepseek=use_deepseek)


def analyze_repo(url: str, 
                 demo_url: str,
                 blog_url: str,
                 paper_url: str,
                 weight_tech_impl: float,
                 weight_arch_design: float,
                 weight_eng_sustain: float,
                 weight_problem_value: float,
                 weight_scenario_innov: float,
                 weight_market_fit: float,
                 use_deepseek: bool,
                 progress=gr.Progress()):
    """
    分析仓库创新性（人性化版本）
    
    Args:
        url: GitHub仓库URL
        demo_url: Demo/官网链接
        blog_url: 技术博客链接
        paper_url: 论文链接
        weight_tech_impl: 技术选型与实现权重
        weight_arch_design: 系统架构与设计权重
        weight_eng_sustain: 工程化与可持续性权重
        weight_problem_value: 问题定义与价值权重
        weight_scenario_innov: 场景创新性权重
        weight_market_fit: 市场与生态契合度权重
        progress: Gradio进度对象
        
    Returns:
        (总分文本, 等级文本, 一句话结论, Markdown报告)
    """
    # 验证URL
    if not url or not url.strip():
        return "❌ 请输入GitHub仓库URL", "", "", ""
    
    url = url.strip()
    if "github.com" not in url.lower():
        return "❌ 请输入有效的GitHub仓库URL", "", "", ""
    
    # 构建权重字典（新版6维度）
    weights = {
        "tech_implementation": weight_tech_impl,
        "architecture_design": weight_arch_design,
        "engineering_sustainability": weight_eng_sustain,
        "problem_value": weight_problem_value,
        "scenario_innovation": weight_scenario_innov,
        "market_fit": weight_market_fit,
    }
    
    # 进度回调
    def progress_callback(prog, message):
        progress(prog, desc=message)
    
    try:
        # 执行分析
        scorer_instance = get_scorer(use_deepseek=use_deepseek)
        report = scorer_instance.analyze(url, weights=weights, progress_callback=progress_callback)
        
        # 生成输出
        score_text = f"**{report.total_score:.1f}** / 100"
        level_text = f"{report.level} {report.level_stars}"
        summary_text = report.core_value_summary or ""
        md_report = scorer_instance.generate_markdown_report(report, use_llm=use_deepseek)
        
        # 添加补充链接到报告末尾
        supplementary_links = []
        if demo_url and demo_url.strip():
            supplementary_links.append(f"- [Demo/官网]({demo_url.strip()})")
        if blog_url and blog_url.strip():
            supplementary_links.append(f"- [技术博客/设计文档]({blog_url.strip()})")
        if paper_url and paper_url.strip():
            supplementary_links.append(f"- [相关论文]({paper_url.strip()})")
        
        if supplementary_links:
            md_report += "\n\n### 团队提供的补充资料\n\n"
            md_report += "\n".join(supplementary_links)
        
        return score_text, level_text, summary_text, md_report
        
    except ValueError as e:
        return f"❌ URL解析错误: {str(e)}", "", "", ""
    except Exception as e:
        return f"❌ 分析失败: {str(e)}", "", "", ""


def reset_weights():
    """重置权重为默认值（6维度框架）"""
    return (
        DEFAULT_WEIGHTS["tech_implementation"],
        DEFAULT_WEIGHTS["architecture_design"],
        DEFAULT_WEIGHTS["engineering_sustainability"],
        DEFAULT_WEIGHTS["problem_value"],
        DEFAULT_WEIGHTS["scenario_innovation"],
        DEFAULT_WEIGHTS["market_fit"],
    )


# 创建Gradio界面
def create_app():
    """创建Gradio应用"""
    
    custom_css = """
    .score-display {
        font-size: 2.5em !important;
        text-align: center;
        padding: 20px;
    }
    .level-display {
        font-size: 1.5em !important;
        text-align: center;
        color: #2563eb;
    }
    .summary-display {
        font-size: 1em !important;
        text-align: center;
        color: #4b5563;
        font-style: italic;
        padding: 10px;
        background: #f3f4f6;
        border-radius: 8px;
        margin-top: 10px;
    }
    """
    
    with gr.Blocks(title="AI应用创新性评估系统") as app:
        
        # 标题
        gr.Markdown("""
        # 🔬 AI应用创新性评估系统（人性化版本 v3.0）
        
        为AI黑客松评委提供自动化的项目创新性评估工具，采用**6维度人性化框架**：
        - **技术创新力（40%）**：技术选型与实现、系统架构与设计、工程化与可持续性
        - **场景创新力（60%）**：问题定义与价值、场景创新性（重点）、市场与生态契合度
        """)
        
        with gr.Row():
            # 左侧：输入区域
            with gr.Column(scale=1):
                # URL输入
                url_input = gr.Textbox(
                    label="GitHub仓库URL",
                    placeholder="https://github.com/owner/repo",
                    info="输入公开的GitHub仓库地址",
                )
                
                # 补充信息（可折叠）
                with gr.Accordion("📎 补充信息（可选）", open=False):
                    gr.Markdown("*提供额外链接可以丰富评估报告*")
                    
                    demo_url = gr.Textbox(
                        label="Demo/官网链接",
                        placeholder="https://example.com/demo",
                        info="在线演示或产品官网",
                    )
                    blog_url = gr.Textbox(
                        label="技术博客/设计文档",
                        placeholder="https://blog.example.com/tech-design",
                        info="详细的技术说明文档",
                    )
                    paper_url = gr.Textbox(
                        label="相关论文链接",
                        placeholder="https://arxiv.org/abs/xxxx.xxxxx",
                        info="arXiv或其他学术论文",
                    )
                
                # 权重配置（可折叠）
                with gr.Accordion("⚙️ 权重配置", open=False):
                    gr.Markdown("""
                    调整各维度在总分中的权重占比（总和自动归一化为100%）
                    
                    **技术创新力（默认40%）**：技术选型13% + 架构设计13% + 工程化14%
                    
                    **场景创新力（默认60%）**：问题价值18% + 场景创新24% + 市场契合18%
                    """)
                    
                    gr.Markdown("##### 技术创新力维度")
                    weight_tech_impl = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["tech_implementation"],
                        step=1, label="技术选型与实现",
                        info="评估使用的技术框架和库的前沿程度、代码实现质量"
                    )
                    weight_arch_design = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["architecture_design"],
                        step=1, label="系统架构与设计",
                        info="评估项目代码结构、设计模式和模块化程度"
                    )
                    weight_eng_sustain = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["engineering_sustainability"],
                        step=1, label="工程化与可持续性",
                        info="评估CI/CD、容器化、测试等工程实践"
                    )
                    
                    gr.Markdown("##### 场景创新力维度")
                    weight_problem_value = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["problem_value"],
                        step=1, label="问题定义与价值",
                        info="评估问题定义清晰度和解决方案的价值主张"
                    )
                    weight_scenario_innov = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["scenario_innovation"],
                        step=1, label="场景创新性 ⭐",
                        info="【重点】评估应用场景的新颖性、是否服务特定人群（如阿尔茨海默症患者）"
                    )
                    weight_market_fit = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["market_fit"],
                        step=1, label="市场与生态契合度",
                        info="评估与技术趋势的契合度、社区认可度和生态集成能力"
                    )
                    
                    reset_btn = gr.Button("🔄 重置为默认权重", size="sm")
                
                # DeepSeek优化开关
                with gr.Accordion("🤖 AI报告优化", open=True):
                    use_deepseek = gr.Checkbox(
                        label="启用DeepSeek模型优化报告",
                        value=True,
                        info="使用DeepSeek-R1模型生成更人性化的评审报告（需要本地vLLM服务）"
                    )
                
                # 分析按钮
                analyze_btn = gr.Button("🚀 开始评估", variant="primary", size="lg")
                
                # 分数显示
                with gr.Group():
                    gr.Markdown("### 📊 评估结果")
                    score_output = gr.Markdown(
                        value="等待评估...",
                        elem_classes=["score-display"]
                    )
                    level_output = gr.Markdown(
                        value="",
                        elem_classes=["level-display"]
                    )
                    # 评委一句话结论
                    summary_output = gr.Markdown(
                        value="",
                        elem_classes=["summary-display"]
                    )
            
            # 右侧：报告区域
            with gr.Column(scale=2):
                gr.Markdown("### 📝 详细报告")
                report_output = gr.Markdown(
                    value="输入GitHub仓库URL并点击「开始评估」查看详细分析报告。",
                )
        
        # 示例URL
        gr.Markdown("""
        ---
        ### 💡 示例仓库（点击填充）
        """)
        examples = gr.Examples(
            examples=[
                ["https://github.com/langchain-ai/langchain"],
                ["https://github.com/openai/openai-python"],
                ["https://github.com/microsoft/autogen"],
                ["https://github.com/run-llama/llama_index"],
            ],
            inputs=[url_input],
            label="热门AI项目",
            cache_examples=False,
        )
        
        # 使用说明
        with gr.Accordion("📖 使用说明", open=False):
            gr.Markdown("""
            ### 评估维度说明（6维度人性化框架）
            
            #### 技术创新力（默认权重40%）
            | 维度 | 权重 | 评分依据 |
            |------|------|----------|
            | 技术选型与实现 | 13% | 使用vLLM、LangChain等前沿库得分高；代码质量、实现规范性 |
            | 系统架构与设计 | 13% | 自定义架构模式得分高，清晰的模块化设计，低耦合高内聚 |
            | 工程化与可持续性 | 14% | CI/CD、Docker、测试覆盖等工程实践完善度 |
            
            #### 场景创新力（默认权重60%）
            | 维度 | 权重 | 评分依据 |
            |------|------|----------|
            | 问题定义与价值 | 18% | 问题定义清晰度、目标用户明确性、价值主张独特性 |
            | **场景创新性** | **24%** | 应用场景新颖性、是否服务特定人群（如阿尔茨海默症患者、残障人士）、跨领域融合 |
            | 市场与生态契合度 | 18% | 技术趋势契合度、社区认可度（Star数）、生态集成能力 |
            
            ### 创新等级
            
            | 分数范围 | 等级 | 说明 |
            |---------|------|------|
            | 90-100 | 突破性创新 ⭐⭐⭐⭐⭐ | 在多个维度展现出卓越的创新性 |
            | 75-89 | 显著创新 ⭐⭐⭐⭐ | 有明确的创新点和技术亮点 |
            | 60-74 | 中等创新 ⭐⭐⭐ | 有一定创新，但仍有提升空间 |
            | 40-59 | 渐进改进 ⭐⭐ | 基于现有方案的小幅改进 |
            | <40 | 常规实现 ⭐ | 标准实现，创新性较低 |
            
            ### 注意事项
            
            - 本工具仅供参考，评估结果应结合人工判断使用
            - **场景创新性**是重点评估维度，聚焦于应用的实际价值和社会影响
            - 支持公开的GitHub仓库，私有仓库需提供访问Token
            - 评估时间取决于仓库大小，通常需要30秒-2分钟
            """)
        
        # 事件绑定
        analyze_btn.click(
            fn=analyze_repo,
            inputs=[url_input, demo_url, blog_url, paper_url, 
                    weight_tech_impl, weight_arch_design, weight_eng_sustain,
                    weight_problem_value, weight_scenario_innov, weight_market_fit,
                    use_deepseek],
            outputs=[score_output, level_output, summary_output, report_output],
            show_progress="full",
        )
        
        reset_btn.click(
            fn=reset_weights,
            outputs=[weight_tech_impl, weight_arch_design, weight_eng_sustain,
                     weight_problem_value, weight_scenario_innov, weight_market_fit],
        )
        
        # 回车触发分析
        url_input.submit(
            fn=analyze_repo,
            inputs=[url_input, demo_url, blog_url, paper_url,
                    weight_tech_impl, weight_arch_design, weight_eng_sustain,
                    weight_problem_value, weight_scenario_innov, weight_market_fit,
                    use_deepseek],
            outputs=[score_output, level_output, summary_output, report_output],
            show_progress="full",
        )
    
    return app, custom_css


# 主入口
if __name__ == "__main__":
    app, css = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        show_error=True,
    )
