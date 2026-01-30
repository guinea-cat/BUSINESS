"""逐步测试导入过程"""
import sys

print(f"Python version: {sys.version}")
print(f"Current directory: {sys.path[0]}")

# 测试1: 导入基础模块
print("\n1. Testing basic modules...")
try:
    import gradio
    print("✓ gradio imported")
except Exception as e:
    print(f"✗ gradio import failed: {e}")

# 测试2: 导入config模块
print("\n2. Testing config module...")
try:
    import config
    print("✓ config imported")
    print(f"DEFAULT_WEIGHTS: {config.DEFAULT_WEIGHTS}")
except Exception as e:
    print(f"✗ config import failed: {e}")

# 测试3: 导入social_value_scorer模块
print("\n3. Testing social_value_scorer module...")
try:
    from core.social_value_scorer import SocialValueScorer
    print("✓ SocialValueScorer imported")
except Exception as e:
    print(f"✗ SocialValueScorer import failed: {e}")
    import traceback
    traceback.print_exc()

print("\nImport test completed!")
