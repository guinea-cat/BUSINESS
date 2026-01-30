#!/usr/bin/env python3
"""
调试应用启动脚本
"""
import traceback
from app import create_app

print("=== 开始调试应用启动 ===")

try:
    print("1. 导入模块成功")
    
    print("2. 创建应用...")
    app, css = create_app()
    print("3. 应用创建成功")
    
    print("4. 启动应用服务器...")
    print("访问地址: http://localhost:7861")
    print("按 Ctrl+C 停止服务器")
    
    # 启动应用
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        show_error=True,
        debug=True
    )
    
    print("5. 应用启动成功")
    
except Exception as e:
    print(f"\n=== 启动失败 ===")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    print("\n详细错误:")
    traceback.print_exc()
    print("\n请检查上述错误信息并解决问题后重试。")
