"""应用启动脚本

使用详细的错误捕获来启动Gradio应用，便于查看启动过程中的错误。
"""
import sys
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("=== 启动AI应用创新性评估系统 ===")
    print(f"Python版本: {sys.version}")
    
    # 导入模块
    print("正在导入模块...")
    from app import create_app
    print("模块导入成功!")
    
    # 创建应用
    print("正在创建应用...")
    app, css = create_app()
    print("应用创建成功!")
    
    # 启动应用
    print("正在启动应用服务器...")
    print("访问地址: http://localhost:7862")
    print("按 Ctrl+C 停止服务器")
    print("================================")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        show_error=True,
        debug=True  # 启用调试模式
    )
    
except Exception as e:
    print(f"\n=== 启动失败 ===")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    print("\n详细错误:")
    traceback.print_exc()
    print("\n请检查上述错误信息并解决问题后重试。")
