"""
app.py
Gradio Web 界面启动脚本。
提供用户友好的 PDF 上传和商业分析结果展示功能。
"""

import json
import gradio as gr
import config
from agent import BusinessResearcher

def process_pdf(file):
    """
    处理上传的 PDF 文件并返回商业潜力分析结果。
    
    参数:
        file: Gradio 的 File 组件返回的文件对象（包含文件路径）。
    
    返回:
        dict 或 str: 如果成功,返回结构化的分析字典；如果失败,返回错误信息字符串。
    
    执行流:
        1. 提取文件路径（Gradio 会自动把上传的文件保存到临时目录）；
        2. 实例化 BusinessResearcher（传入 LLM API Key）；
        3. 调用 analyze_business_potential 方法执行完整分析流程；
        4. 如果成功，返回字典供 gr.JSON 组件渲染；
        5. 如果失败，返回错误信息字符串。
    
    为什么要单独写这个函数？
        Gradio 的交互逻辑是"函数式"的：每个组件的变化都会触发一个 Python 函数，
        并将返回值自动渲染到界面上。这个函数就是连接"用户操作"和"后端逻辑"的桥梁。
    """
    try:
        # 步骤 1: 提取文件路径
        # Gradio 的 File 组件返回的 file 对象有一个 name 属性，存储临时文件路径
        if file is None:
            return {"error": "请先上传 PDF 文件"}
        
        pdf_path = file.name
        print(f"[INFO] 接收到文件: {pdf_path}")
        
        # 步骤 2: 实例化智能体
        researcher = BusinessResearcher(config.LLM_API_KEY)
        
        # 步骤 3: 执行分析
        result = researcher.analyze_business_potential(pdf_path)
        
        # 步骤 4: 返回结果
        # Gradio 会自动将字典渲染为美化的 JSON
        return result
        
    except Exception as e:
        # 如果出现未捕获的异常，返回错误信息
        return {
            "error": "处理失败",
            "details": str(e)
        }

def main():
    """
    构建并启动 Gradio 界面。
    
    界面设计哲学:
        1. 简洁明了：用户一眼就能看懂如何操作；
        2. 实时反馈：每个步骤都有状态提示（如"分析中..."）；
        3. 结果可读：使用 JSON 组件自动美化输出。
    
    组件选择理由:
        - gr.File: 专为文件上传设计，支持拖拽和点击选择；
        - gr.Button: 显式的触发按钮，让用户掌控分析时机；
        - gr.JSON: 自动将 Python 字典渲染为可展开/折叠的树状结构。
    """
    # 使用 Blocks 构建自定义布局
    # Blocks 是 Gradio 的高级 API，允许我们精细控制组件的位置和交互逻辑
    with gr.Blocks(
        title="SAGE - 商业潜力 AI 评测",
        theme=gr.themes.Soft()  # 使用柔和主题
    ) as demo:
        
        # 标题和说明
        gr.Markdown(
            """
            # 🚀 SAGE - 商业潜力 AI 评测
            ### Powered by DeepSeek & Serper.dev
            
            上传您的商业计划书（PDF 格式），我们的 AI 智能体将：
            1. 📊 提取核心关键词
            2. 🌐 联网搜索市场情报
            3. 🧠 基于 VC 视角深度分析商业潜力
            """
        )
        
        # 使用 Row 实现左右分栏布局
        with gr.Row():
            # 左侧：输入区域
            with gr.Column(scale=1):
                gr.Markdown("### 📁 上传文件")
                file_input = gr.File(
                    label="商业计划书 (PDF)",
                    file_types=[".pdf"],  # 限制只能上传 PDF
                    type="filepath"  # 返回文件路径而非二进制数据
                )
                
                analyze_btn = gr.Button(
                    "🔍 开始深度分析",
                    variant="primary",  # 主要按钮样式（蓝色高亮）
                    size="lg"  # 大尺寸按钮
                )
                
                gr.Markdown(
                    """
                    **注意事项：**
                    - 分析时间约 30-60 秒
                    - 确保 PDF 可正常提取文本
                    - 请勿上传敏感商业信息
                    """
                )
            
            # 右侧：输出区域
            with gr.Column(scale=2):
                gr.Markdown("### 📈 分析报告")
                output_json = gr.JSON(
                    label="结构化分析结果",
                    show_label=False
                )
        
        # 绑定交互逻辑
        # 当用户点击按钮时，触发 process_pdf 函数
        # inputs: 指定函数的输入参数来自哪个组件
        # outputs: 指定函数的返回值要更新哪个组件
        analyze_btn.click(
            fn=process_pdf,
            inputs=file_input,
            outputs=output_json
        )
        
        # 添加示例（可选）
        gr.Markdown(
            """
            ---
            **技术栈：** Python + DeepSeek API + Serper.dev + Gradio  
            **开发者提示：** 查看终端输出可以看到详细的执行日志
            """
        )
    
    # 启动应用
    # share=True 会生成公网链接（72 小时有效），方便分享
    # server_name="0.0.0.0" 允许局域网访问
    demo.launch(
        share=False,  # 不生成公网链接（仅本地开发）
        server_name="127.0.0.1",  # 仅本地访问
        server_port=8080,  # 改用 8080 端口
        inbrowser=True  # 自动打开浏览器
    )

if __name__ == "__main__":
    main()
