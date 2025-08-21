#!/usr/bin/env python3
"""
测试模型自动适配功能
"""

import degpt as dg

def test_model_auto_adjust():
    """测试模型自动适配"""
    print("=== 测试模型自动适配功能 ===")
    
    # 先获取模型列表
    models_str = dg.get_models()
    print(f"可用模型: {models_str[:200]}...")
    
    # 测试存在的模型
    print("\n1. 测试存在的模型:")
    real_model = "gpt-4o-mini"  # 假设这个模型存在
    result = dg.get_model_by_autoupdate(real_model)
    print(f"输入: {real_model} -> 输出: {result}")
    
    # 测试不存在的模型
    print("\n2. 测试不存在的模型:")
    fake_model = "non-existent-model-123"
    result = dg.get_model_by_autoupdate(fake_model)
    print(f"输入: {fake_model} -> 输出: {result}")
    
    # 测试auto模式
    print("\n3. 测试auto模式:")
    result = dg.get_auto_model()
    print(f"auto模式 -> 输出: {result}")
    
    # 测试None输入
    print("\n4. 测试None输入:")
    result = dg.get_model_by_autoupdate(None)
    print(f"输入: None -> 输出: {result}")

def test_model_availability():
    """测试模型可用性检查"""
    print("\n=== 测试模型可用性检查 ===")
    
    # 测试存在的模型
    real_model = "gpt-4o-mini"
    available = dg.is_model_available(real_model)
    print(f"模型 {real_model} 可用: {available}")
    
    # 测试不存在的模型
    fake_model = "non-existent-model-123"
    available = dg.is_model_available(fake_model)
    print(f"模型 {fake_model} 可用: {available}")

if __name__ == "__main__":
    print("开始测试模型自动适配功能...")
    
    test_model_auto_adjust()
    test_model_availability()
    
    print("\n=== 测试完成 ===")