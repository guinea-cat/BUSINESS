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
    import re
    
    if "error" in data:
        return f"# ⚠️ 错误\n\n{data.get('error')}\n\n**详细信息**: {data.get('details', 'N/A')}"
    
    # 辅助函数：将 [S1] 转换为上标格式
    def cite_repl(match):
        return f"<sup>{match.group(0)}</sup>"
    
    def process_citations(text: str) -> str:
        if not isinstance(text, str): return str(text)
        return re.sub(r"\[S\d+\]", cite_repl, text)

    md = "# 📊 科创大赛 AI 评审 - 深度商业分析报告\n\n---\n\n"
    
    # 1. 项目深度画像
    pi = data.get("project_identity", {})
    md += f"## 🚀 项目本体画像 (Project Identity)\n"
    md += f"**项目名称**: {pi.get('project_name', 'N/A')}\n\n"
    md += f"**核心愿景**: *{pi.get('slogan', 'N/A')}*\n\n"
    md += f"### 📝 深度描述\n{process_citations(pi.get('description', 'N/A'))}\n\n"
    md += f"### 💰 盈利模式\n{process_citations(pi.get('revenue_model', 'N/A'))}\n\n"
    md += f"### 👥 团队背景优势\n{process_citations(pi.get('team_background', 'N/A'))}\n\n"
    md += f"- **发展阶段**: `{pi.get('stage', 'N/A')}`\n\n"
    
    # 2. 赛道与市场
    ia = data.get("industry_analysis", {})
    md += "## 🌐 赛道分析与市场量化\n"
    md += f"- **识别赛道**: {ia.get('detected_industry', 'N/A')}\n"
    md += f"- **市场规模**: {process_citations(ia.get('market_size', 'Not Found'))}\n"
    md += f"- **复合增长率 (CAGR)**: {process_citations(ia.get('cagr', 'Not Found'))}\n"
    md += f"- **数据来源**: {ia.get('source', 'N/A')}\n\n"

    # 3. 商业深度拆解
    ba = data.get("business_analysis", {})
    md += "## ⚖️ 商业深度拆解\n"
    md += f"### 🏢 商业模式可行性评述\n{process_citations(ba.get('business_model_critique', 'N/A'))}\n\n"
    md += f"### 🛡️ 技术壁垒与护城河\n{process_citations(ba.get('technical_moat', 'N/A'))}\n\n"
    
    # 4. VC 灵魂拷问 (新模块)
    vg = data.get("vc_grill", [])
    if vg:
        md += "## 🔥 VC 灵魂拷问 (The VC Grill)\n"
        for item in vg:
            md += f"**Q: {item.get('question')}**\n\n"
            md += f"**A:** {process_citations(item.get('answer'))}\n\n"
    
    # 5. 竞品
    md += "## 🎯 竞争格局与替代品\n"
    for comp in data.get("competitors", []):
        md += f"### 🏢 {comp.get('name')}\n- **类型**: {comp.get('type')}\n- **分析**: {process_citations(comp.get('comparison'))}\n\n"
    
    # 6. 融资与舆情
    fe = data.get("funding_ecosystem", {})
    ps = data.get("public_sentiment", {})
    md += f"## 💹 融资生态 & 舆情研判\n"
    md += f"- **资本热度**: `{fe.get('heat_level', 'N/A')}`\n"
    md += f"- **动态摘要**: {process_citations(fe.get('trend_summary', 'N/A'))}\n"
    md += f"- **舆情倾向**: {ps.get('label')} — {process_citations(ps.get('summary'))}\n\n"
    
    # 7. 风险
    md += "## ⚠️ 核心风险识别\n"
    for risk in data.get("risk_assessment", []):
        md += f"- {process_citations(risk)}\n"
    
    # 8. 数据来源与参考文献
    md += "\n---\n## 🔗 数据来源与参考文献\n"
    evidence = data.get("raw_evidence", [])
    if evidence:
        for item in evidence:
            eid = item.get('id', 'N/A')
            md += f"- **[{eid}] {item.get('source')}**: [{item.get('url')}]({item.get('url')})\n"
    else:
        md += "- 暂无外部参考链接。\n"
    
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
