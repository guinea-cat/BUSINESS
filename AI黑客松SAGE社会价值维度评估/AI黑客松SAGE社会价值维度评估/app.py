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
                 weight_basic_ethics: float,
                 weight_social_impact: float,
                 weight_environmental_friendliness: float,
                 weight_charity_orientation: float,
                 weight_long_term_vision: float,
                 use_deepseek: bool,
                 progress=gr.Progress()):
    """
    分析仓库社会价值（AI黑客松版本 20/80 体系）
    """
    # 验证URL
    if not url or not url.strip():
        return "❌ 请输入GitHub仓库URL", "", "", ""
    
    url = url.strip()
    if "github.com" not in url.lower():
        return "❌ 请输入有效的GitHub仓库URL", "", "", ""
    
    # 构建权重字典
    weights = {
        "basic_ethics": weight_basic_ethics,
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
    """重置权重为默认值（社会价值评估 20/80 体系）"""
    return (
        DEFAULT_WEIGHTS["basic_ethics"],
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
                    根据 AI 黑客松评分标准调整权重占比
                    
                    **基础项（20分）**：伦理、隐私与公平性底线检查
                    
                    **核心亮点项（80分）**：从四个维度中选择最突出的一个进行深度评估
                    """)
                    
                    gr.Markdown("##### 基础项评估权重")
                    weight_basic_ethics = gr.Slider(
                        minimum=0, maximum=20, value=DEFAULT_WEIGHTS["basic_ethics"],
                        step=1, label="基础项总分（底线检查）",
                        info="无问题得20分，发现风险按严重程度扣分"
                    )
                    
                    gr.Markdown("##### 核心亮点项评估权重")
                    weight_social_impact = gr.Slider(
                        minimum=0, maximum=80, value=DEFAULT_WEIGHTS["social_impact"],
                        step=1, label="A. 社会影响深度",
                        info="解决具体社会问题、服务特定群体"
                    )
                    weight_environmental_friendliness = gr.Slider(
                        minimum=0, maximum=80, value=DEFAULT_WEIGHTS["environmental_friendliness"],
                        step=1, label="B. 环境可持续性",
                        info="环保、节能、低碳、绿色设计"
                    )
                    weight_charity_orientation = gr.Slider(
                        minimum=0, maximum=80, value=DEFAULT_WEIGHTS["charity_orientation"],
                        step=1, label="C. 公益普惠导向",
                        info="普惠性、可及性、包容性、公益优先"
                    )
                    weight_long_term_vision = gr.Slider(
                        minimum=0, maximum=80, value=DEFAULT_WEIGHTS["long_term_vision"],
                        step=1, label="D. 长期愿景与变革潜力",
                        info="愿景清晰度、系统性变革潜力、实施路径"
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
            ### 评估维度说明（20/80 评分体系）
            
            #### 一、 基础项评估（20分，底线检查）
            基础项仅检查是否存在问题，符合要求得满分20分。
            - **伦理红线检查**：是否触及公认伦理红线（触及即本维度不及格）
            - **隐私与数据保护**：是否有明显隐私风险（扣3-10分）
            - **算法公平性**：是否有明显不公平设计（扣3-10分）
            
            #### 二、 核心亮点项评估（80分）
            系统将自动从以下四个维度中，根据项目特点选择**最突出的1个**进行深度评估：
            - **A. 社会影响深度**：解决具体社会问题、服务特定群体
            - **B. 环境可持续性**：环保、节能、可持续发展
            - **C. 公益普惠导向**：普惠性、可及性、非营利性
            - **D. 长期愿景与变革潜力**：系统性变革、先进价值取向
            
            ### 总分与等级
            | 分数范围 | 等级 | 说明 |
            |---------|------|------|
            | 90-100 | 卓越 | 社会价值显著，亮点突出 |
            | 80-89 | 优秀 | 社会价值明确，表现良好 |
            | 70-79 | 良好 | 有一定社会价值 |
            | 60-69 | 合格 | 基本符合要求 |
            | <60 | 待改进 | 社会价值不足 |
            
            ### 评估流程
            1. **基础项检查**：底线合规性分析
            2. **识别核心维度**：匹配项目最突出的社会贡献点
            3. **深度专家评审**：模拟真人评审，输出具行业洞察力的详尽报告
            """)
        
        # 事件绑定
        analyze_btn.click(
            fn=analyze_repo,
            inputs=[url_input, demo_url, blog_url, paper_url, 
                    weight_basic_ethics,
                    weight_social_impact, weight_environmental_friendliness, weight_charity_orientation, weight_long_term_vision,
                    use_deepseek],
            outputs=[score_output, level_output, summary_output, report_output],
            show_progress="full",
        )
        
        reset_btn.click(
            fn=reset_weights,
            outputs=[weight_basic_ethics, 
                     weight_social_impact, weight_environmental_friendliness, weight_charity_orientation, weight_long_term_vision],
        )
        
        # 回车触发分析
        url_input.submit(
            fn=analyze_repo,
            inputs=[url_input, demo_url, blog_url, paper_url,
                    weight_basic_ethics,
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
