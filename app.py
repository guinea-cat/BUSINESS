"""
app.py
Gradio Web 界面演示。
"""

import os
import gradio as gr
import config
import logging
import time
from datetime import datetime
from agent import BusinessResearcher

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_analysis(file_obj):
    """
    处理上传文件并调用分析流水线。
    使用 yield 机制实时返回进度状态（优化用户体验）。
    """
    if file_obj is None:
        yield "# ⚠️ 请先上传 PDF 文件", {}, None
        return
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        pdf_path = file_obj.name
        researcher = BusinessResearcher(config.LLM_API_KEY)
        
        # 阶段 1：PDF 解析
        elapsed = time.time() - start_time
        yield f"## 📄 正在解析 PDF 与图片... (已耗时 {elapsed:.1f}s)\n\n请稍候，系统正在提取文本内容和视觉元素。", {}, None
        
        import utils
        pdf_content = utils.extract_content_from_pdf(pdf_path)
        bp_full_text = pdf_content["text"]
        bp_images = pdf_content["images"]
        
        # 阶段 2：视觉分析
        if bp_images:
            elapsed = time.time() - start_time
            yield f"## 🖼️ 正在并发视觉分析... (已耗时 {elapsed:.1f}s)\n\n检测到 {len(bp_images)} 张图片，正在进行 2x2 拼图与并发分析。", {}, None
            visual_descriptions = utils.describe_visual_elements(researcher.vision_client, bp_images)
        else:
            visual_descriptions = ""
        
        # 阶段 3-4：赛道感知与关键词生成（合并优化）
        elapsed = time.time() - start_time
        yield f"## 🎯 正在进行赛道感知与关键词生成... (已耗时 {elapsed:.1f}s)\n\n【性能优化】单次 LLM 调用同时完成赛道识别和关键词生成，节省 2-3 秒。", {}, None
        
        # 阶段 5：并发 JSON 生成
        elapsed = time.time() - start_time
        yield f"## 🧠 正在生成最终研报... (已耗时 {elapsed:.1f}s)\n\n并发执行 **4 路并发分析**：\n- 基础信息组（项目画像 + 赛道分析）\n- 外部情报组（竞品 + 融资生态）\n- **估值模型组**（VC 评分）\n- **风险评估组**（拷问 + 痛点 + 风险）", {}, None
        
        # 调用完整的分析流水线
        result = researcher.analyze_bp_pipeline(pdf_path)
        
        # 计算总耗时
        total_time = time.time() - start_time
        
        # 格式化 Markdown 报告（包含总耗时）
        markdown_report = format_markdown(result, total_time)
        
        # --- 新增：保存并导出 MD 文件 ---
        # 确保输出目录存在
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 构造文件名：项目名_研报_时间戳.md
        project_name = result.get("project_identity", {}).get("project_name", "未知项目")
        # 清洗文件名中的非法字符
        safe_project_name = "".join([c for c in project_name if c.isalnum() or c in (" ", "_", "-")]).strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{safe_project_name}_研报_{timestamp}.md"
        file_path = os.path.abspath(os.path.join(output_dir, file_name))
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_report)
            
        logger.info(f"研报已成功保存至: {file_path}")
        # -----------------------------
        
        yield markdown_report, result, file_path
        
    except Exception as e:
        logger.error(f"UI 处理异常: {e}")
        yield f"# ❌ 系统处理异常\n{str(e)}", {"status": "error"}, None

def format_markdown(data: dict, total_time: float = 0) -> str:
    """
    将分析结果 JSON 转换为 Markdown 研报。
    
    参数:
        data: 分析结果字典
        total_time: 总耗时（秒）
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
    # md += f"### 👥 团队背景优势\n{process_citations(pi.get('team_background', 'N/A'))}\n\n"
    md += f"- **发展阶段**: `{pi.get('stage', 'N/A')}`\n\n"
    
    # 2. 赛道与市场
    ia = data.get("industry_analysis", {})
    md += "## 🌐 赛道分析与市场量化\n"
    md += f"- **识别赛道**: {ia.get('detected_industry', 'N/A')}\n"
    # md += f"- **市场规模**: {process_citations(ia.get('market_size', 'Not Found'))}\n"
    # md += f"- **复合增长率 (CAGR)**: {process_citations(ia.get('cagr', 'Not Found'))}\n"
    # md += f"- **数据来源**: {ia.get('source', 'N/A')}\n\n"

    # 3. 商业深度拆解
    ba = data.get("business_analysis", {})
    md += "## ⚖️ 商业深度拆解\n"
    md += f"### 🏢 商业模式可行性评述\n{process_citations(ba.get('business_model_critique', 'N/A'))}\n\n"
    md += f"### 🛡️ 技术壁垒与护城河\n{process_citations(ba.get('technical_moat', 'N/A'))}\n\n"
    
    # 4. 商业潜力量化评估 (新增)
    vm = data.get("valuation_model", {})
    if vm:
        md += f"## 💎 商业潜力量化评估 (Valuation Model)\n"
        md += f"**综合评分**: `{vm.get('total_score', 'N/A')}` | **投资评级**: `{vm.get('rating', 'N/A')}`\n\n"
        md += f"> **核心摘要**: {process_citations(vm.get('summary', 'N/A'))}\n\n"
        
        md += "| 评估维度 | 分数 | 满分 | 核心分析 |\n"
        md += "| :--- | :--- | :--- | :--- |\n"
        
        dimensions = vm.get("dimensions", {})
        dim_map = {
            "market": "市场潜力",
            "product": "产品与技术",
            "business_model": "商业模式",
            "team": "团队竞争力",
            "execution": "验证与风险"
        }
        
        for key, label in dim_map.items():
            d = dimensions.get(key, {})
            score = d.get("score", "N/A")
            max_s = d.get("max_score", "N/A")
            analysis = process_citations(d.get("analysis", "N/A"))
            md += f"| {label} | {score} | {max_s} | {analysis} |\n"
        md += "\n"

    # 5. VC 灵魂拷问
    vg = data.get("vc_grill", [])
    if vg:
        md += "## 🔥 VC 灵魂拷问 (The VC Grill)\n"
        for item in vg:
            md += f"**Q: {item.get('question')}**\n\n"
            md += f"**A:** {process_citations(item.get('answer'))}\n\n"
    
    # 6. 痛点真实性验证 (新增)
    ppv = data.get("pain_point_validation", {})
    if ppv:
        md += "## 🎯 痛点真实性验证\n"
        md += f"**真实性评分**: `{ppv.get('score', 'N/A')}/10`\n\n"
        md += f"**评估逻辑**: {process_citations(ppv.get('reason', 'N/A'))}\n\n"

    # 7. 竞品
    md += "## 🎯 竞争格局与替代品\n"
    for comp in data.get("competitors", []):
        md += f"### 🏢 {comp.get('name')}\n- **类型**: {comp.get('type')}\n- **分析**: {process_citations(comp.get('comparison'))}\n\n"
    
    # 8. 融资与舆情
    fe = data.get("funding_ecosystem", {})
    ps = data.get("public_sentiment", {})
    md += f"## 💹 融资生态 & 舆情研判\n"
    md += f"- **资本热度**: `{fe.get('heat_level', 'N/A')}`\n"
    md += f"- **动态摘要**: {process_citations(fe.get('trend_summary', 'N/A'))}\n"
    md += f"- **舆情倾向**: {ps.get('label')} — {process_citations(ps.get('summary'))}\n\n"
    
    # 9. 风险
    md += "## ⚠️ 核心风险识别\n"
    for risk in data.get("risk_assessment", []):
        md += f"- {process_citations(risk)}\n"
    
    # 10. 数据来源与参考文献
    md += "\n---\n## 🔗 数据来源与参考文献\n"
    evidence = data.get("raw_evidence", [])
    if evidence:
        for item in evidence:
            eid = item.get('id', 'N/A')
            md += f"- **[{eid}] {item.get('source')}**: [{item.get('url')}]({item.get('url')})\n"
    else:
        md += "- 暂无外部参考链接。\n"
    
    md += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    md += f"*本次分析总耗时: {total_time:.1f} 秒*"
    return md

def main():
    with gr.Blocks(title="SAGE Business Analysis", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🚀 SAGE 商业潜力 AI 评测系统\n基于 DeepSeek & Serper.dev 的全行业通用分析引擎。")
        
        with gr.Row():
            with gr.Column(scale=1):
                pdf_input = gr.File(label="上传 BP (PDF)", file_types=[".pdf"])
                btn = gr.Button("开始全自动分析", variant="primary")
                out_file = gr.File(label="📥 下载研报 (.md)", interactive=False)
                gr.Markdown("### ⚙️ 说明\n- 系统将自动识别赛道并进行全网情报检索。\n- 分析耗时预计 45-60 秒。")
                
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.Tab("📝 研报视图"):
                        out_md = gr.Markdown("等待分析...")
                    with gr.Tab("📊 原始数据"):
                        out_json = gr.JSON()
        
        btn.click(fn=run_analysis, inputs=pdf_input, outputs=[out_md, out_json, out_file], api_name=False)
    
    demo.launch(server_port=8081, inbrowser=True)

if __name__ == "__main__":
    main()
