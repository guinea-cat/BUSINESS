"""
app.py
Gradio Web 界面演示。
"""

import gradio as gr
import config
import logging
from agent import BusinessResearcher

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_analysis(file_obj):
    """
    处理上传文件并调用分析流水线。
    """
    if file_obj is None:
        return "# ⚠️ 请先上传 PDF 文件", {}
    
    try:
        pdf_path = file_obj.name
        researcher = BusinessResearcher(config.LLM_API_KEY)
        
        # 调用核心流水线方法
        result = researcher.analyze_bp_pipeline(pdf_path)
        
        # 格式化 Markdown 报告
        markdown_report = format_markdown(result)
        return markdown_report, result
        
    except Exception as e:
        logger.error(f"UI 处理异常: {e}")
        return f"# ❌ 系统处理异常\n{str(e)}", {"status": "error"}

def format_markdown(data: dict) -> str:
    """
    将分析结果 JSON 转换为 Markdown 研报。
    """
    from datetime import datetime
    
    if "error" in data:
        return f"# ⚠️ 错误\n\n{data.get('error')}\n\n**详细信息**: {data.get('details', 'N/A')}"
    
    md = "# 📊 科创大赛 AI 评审 - 商业潜力分析报告\n\n---\n\n"
    
    # 赛道与市场
    ia = data.get("industry_analysis", {})
    md += f"## 🌐 赛道与市场数据\n- **识别赛道**: {ia.get('detected_industry', 'N/A')}\n"
    md += f"- **市场规模**: {ia.get('market_size', 'Not Found')}\n"
    md += f"- **复合增长率 (CAGR)**: {ia.get('cagr', 'Not Found')}\n"
    md += f"- **数据来源**: {ia.get('source', 'N/A')}\n\n"
    
    # 竞品
    md += "## 🎯 竞争格局与替代品\n"
    for comp in data.get("competitors", []):
        md += f"### 🏢 {comp.get('name')}\n- **类型**: {comp.get('type')}\n- **分析**: {comp.get('comparison')}\n\n"
    
    # 融资
    fe = data.get("funding_ecosystem", {})
    md += f"## 💰 融资生态\n- **热度评级**: {fe.get('heat_level', 'N/A')}\n- **趋势摘要**: {fe.get('trend_summary', 'N/A')}\n\n"
    
    # 痛点
    pv = data.get("pain_point_validation", {})
    md += f"## 🧠 痛点验证\n- **分值**: {pv.get('score')}/10\n- **依据**: {pv.get('reason')}\n\n"
    
    # 舆情
    ps = data.get("public_sentiment", {})
    md += f"## 💬 公众舆情\n- **情感**: {ps.get('label')}\n- **摘要**: {ps.get('summary')}\n\n"
    
    # 风险
    md += "## ⚠️ 核心风险识别\n"
    for risk in data.get("risk_assessment", []):
        md += f"- {risk}\n"
    
    md += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    return md

def main():
    with gr.Blocks(title="SAGE Business Analysis", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🚀 SAGE 商业潜力 AI 评测系统\n基于 DeepSeek & Serper.dev 的全行业通用分析引擎。")
        
        with gr.Row():
            with gr.Column(scale=1):
                pdf_input = gr.File(label="上传 BP (PDF)", file_types=[".pdf"])
                btn = gr.Button("开始全自动分析", variant="primary")
                gr.Markdown("### ⚙️ 说明\n- 系统将自动识别赛道并进行全网情报检索。\n- 分析耗时预计 45-60 秒。")
                
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.Tab("📝 研报视图"):
                        out_md = gr.Markdown("等待分析...")
                    with gr.Tab("📊 原始数据"):
                        out_json = gr.JSON()
        
        btn.click(fn=run_analysis, inputs=pdf_input, outputs=[out_md, out_json])
    
    demo.launch(server_port=8081, inbrowser=True)

if __name__ == "__main__":
    main()
