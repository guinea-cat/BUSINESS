"""AI黑客松社会价值评估系统 - Gradio界面

功能：
- URL输入框
- 7维度权重配置（基础项30% + 加分项70%）
- 评估按钮+进度显示
- 人性化Markdown报告展示
"""
import gradio as gr
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config import DEFAULT_WEIGHTS
from core.social_value_scorer import SocialValueScorer


# 全局评分器实例
scorer = None

def get_scorer(use_deepseek: bool = True):
    """获取或创建评分器实例"""
    global scorer
    if scorer is None:
        scorer = SocialValueScorer(use_deepseek=use_deepseek)
    return scorer


def analyze_repo(url: str, 
                 demo_url: str,
                 blog_url: str,
                 paper_url: str,
                 weight_ethics_redline: float,
                 weight_privacy_protection: float,
                 weight_algorithm_fairness: float,
                 weight_social_impact: float,
                 weight_environmental_friendliness: float,
                 weight_charity_orientation: float,
                 weight_long_term_vision: float,
                 use_deepseek: bool,
                 progress=gr.Progress()):
    """
    分析仓库社会价值（AI黑客松版本）
    
    Args:
        url: GitHub仓库URL
        demo_url: Demo/官网链接
        blog_url: 技术博客链接
        paper_url: 论文链接
        weight_ethics_redline: 伦理红线检查权重
        weight_privacy_protection: 隐私与数据保护权重
        weight_algorithm_fairness: 算法公平性意识权重
        weight_social_impact: 社会影响深度权重
        weight_environmental_friendliness: 环境可持续性权重
        weight_charity_orientation: 公益普惠导向权重
        weight_long_term_vision: 长期愿景与变革潜力权重
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
    
    # 构建权重字典（新版7维度）
    weights = {
        "ethics_redline": weight_ethics_redline,
        "privacy_protection": weight_privacy_protection,
        "algorithm_fairness": weight_algorithm_fairness,
        "social_impact": weight_social_impact,
        "environmental_friendliness": weight_environmental_friendliness,
        "charity_orientation": weight_charity_orientation,
        "long_term_vision": weight_long_term_vision,
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
    """重置权重为默认值（社会价值评估7维度框架）"""
    return (
        DEFAULT_WEIGHTS["ethics_redline"],
        DEFAULT_WEIGHTS["privacy_protection"],
        DEFAULT_WEIGHTS["algorithm_fairness"],
        DEFAULT_WEIGHTS["social_impact"],
        DEFAULT_WEIGHTS["environmental_friendliness"],
        DEFAULT_WEIGHTS["charity_orientation"],
        DEFAULT_WEIGHTS["long_term_vision"],
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
    
    with gr.Blocks(title="AI黑客松社会价值评估系统") as app:
        
        # 标题
        gr.Markdown("""
        # 🌟 AI黑客松社会价值评估系统
        
        为AI黑客松评委提供自动化的项目社会价值评估工具，采用**基础项+加分项架构**：
        - **基础项（30%）**：伦理安全合规性 - 必须评估的部分
        - **加分项（70%）**：社会影响、环境友好、公益导向、长期愿景 - 根据项目特点选择性突出
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
                    
                    **基础项（默认30%）**：伦理红线检查10% + 隐私与数据保护10% + 算法公平性意识10%
                    
                    **加分项（默认70%）**：社会影响深度25% + 环境可持续性15% + 公益普惠导向15% + 长期愿景与变革潜力15%
                    """)
                    
                    gr.Markdown("##### 基础项：伦理安全合规性")
                    weight_ethics_redline = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["ethics_redline"],
                        step=1, label="伦理红线检查",
                        info="评估项目是否触及公认的AI伦理红线"
                    )
                    weight_privacy_protection = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["privacy_protection"],
                        step=1, label="隐私与数据保护",
                        info="评估对用户隐私和数据权利的基本尊重"
                    )
                    weight_algorithm_fairness = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["algorithm_fairness"],
                        step=1, label="算法公平性意识",
                        info="评估是否考虑了算法可能产生的不公平后果"
                    )
                    
                    gr.Markdown("##### 加分项：社会价值亮点")
                    weight_social_impact = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["social_impact"],
                        step=1, label="社会影响深度 ⭐",
                        info="【重点】评估项目对社会问题的解决程度和受益群体范围"
                    )
                    weight_environmental_friendliness = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["environmental_friendliness"],
                        step=1, label="环境可持续性",
                        info="评估项目的环境友好程度和可持续发展理念"
                    )
                    weight_charity_orientation = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["charity_orientation"],
                        step=1, label="公益普惠导向",
                        info="评估项目的公益性质和普惠性设计"
                    )
                    weight_long_term_vision = gr.Slider(
                        minimum=0, maximum=100, value=DEFAULT_WEIGHTS["long_term_vision"],
                        step=1, label="长期愿景与变革潜力",
                        info="评估项目的长期发展愿景和系统变革潜力"
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
            ### 评估维度说明（基础项+加分项架构）
            
            #### 基础项：伦理安全合规性（默认30%）
            | 维度 | 权重 | 评分依据 |
            |------|------|----------|
            | 伦理红线检查 | 10% | 项目是否触及公认的AI伦理红线 |
            | 隐私与数据保护 | 10% | 对用户隐私和数据权利的基本尊重 |
            | 算法公平性意识 | 10% | 是否考虑了算法可能产生的不公平后果 |
            
            #### 加分项：社会价值亮点（默认70%）
            | 维度 | 权重 | 评分依据 |
            |------|------|----------|
            | 社会影响深度 | 25% | 问题解决程度、受益群体范围、影响可扩展性 |
            | 环境可持续性 | 15% | 直接环境效益、绿色设计理念、意识提升作用 |
            | 公益普惠导向 | 15% | 普惠性设计、公益优先性、包容性考量 |
            | 长期愿景与变革潜力 | 15% | 愿景清晰度与合理性、系统性变革潜力、实施路径可行性 |
            
            ### 社会价值等级
            
            | 分数范围 | 等级 | 说明 |
            |---------|------|------|
            | 90-100 | 卓越社会价值 ⭐⭐⭐⭐⭐ | 在多个维度展现出卓越的社会价值 |
            | 75-89 | 显著社会价值 ⭐⭐⭐⭐ | 有明确的社会价值亮点和贡献 |
            | 60-74 | 良好社会价值 ⭐⭐⭐ | 有一定社会价值，但仍有提升空间 |
            | 40-59 | 一般社会价值 ⭐⭐ | 社会价值有限，需要进一步发展 |
            | <40 | 社会价值有限 ⭐ | 社会价值不明显，需要重新定位 |
            
            ### 注意事项
            
            - 本工具仅供参考，评估结果应结合人工判断使用
            - **社会影响深度**是重点评估维度，聚焦于应用的实际社会价值
            - 支持公开的GitHub仓库，私有仓库需提供访问Token
            - 评估时间取决于仓库大小，通常需要30秒-2分钟
            """)
        
        # 事件绑定
        analyze_btn.click(
            fn=analyze_repo,
            inputs=[url_input, demo_url, blog_url, paper_url, 
                    weight_ethics_redline, weight_privacy_protection, weight_algorithm_fairness,
                    weight_social_impact, weight_environmental_friendliness, weight_charity_orientation, weight_long_term_vision,
                    use_deepseek],
            outputs=[score_output, level_output, summary_output, report_output],
            show_progress="full",
        )
        
        reset_btn.click(
            fn=reset_weights,
            outputs=[weight_ethics_redline, weight_privacy_protection, weight_algorithm_fairness,
                     weight_social_impact, weight_environmental_friendliness, weight_charity_orientation, weight_long_term_vision],
        )
        
        # 回车触发分析
        url_input.submit(
            fn=analyze_repo,
            inputs=[url_input, demo_url, blog_url, paper_url,
                    weight_ethics_redline, weight_privacy_protection, weight_algorithm_fairness,
                    weight_social_impact, weight_environmental_friendliness, weight_charity_orientation, weight_long_term_vision,
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
