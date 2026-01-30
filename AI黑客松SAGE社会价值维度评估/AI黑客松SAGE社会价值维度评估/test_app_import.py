"""测试app.py导入"""
import sys
import traceback

print("Testing app.py import...")

try:
    # 测试导入app模块
    import app
    print("✓ app module imported successfully")
    
    # 测试create_app函数
    from app import create_app
    print("✓ create_app function imported successfully")
    
    # 测试创建应用
    app_instance, css = create_app()
    print("✓ App created successfully")
    
    print("\nAll tests passed!")
    
except Exception as e:
    print(f"\n✗ Test failed with error: {e}")
    print("\nDetailed error:")
    traceback.print_exc()
