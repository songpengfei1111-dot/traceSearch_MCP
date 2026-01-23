#!/usr/bin/env python3
"""Large Text Searcher Skill 测试脚本"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from large_text_searcher import (
    get_file_info,
    extract_lines,
    search_text,
    search_crypto_magic,
    LargeTextSearcherError
)


def test_skill_functions():
    """测试skill的基本功能"""
    print("=== Large Text Searcher Skill 测试 ===\n")
    
    # 测试文件路径 - 使用项目根目录的readme.md作为测试文件
    test_file = "../../../readme.md"
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return
    
    try:
        # 测试文件信息获取
        print("1. 测试文件信息获取:")
        file_info = get_file_info(test_file)
        print(file_info)
        print()
        
        # 测试行提取
        print("2. 测试行提取 (前10行):")
        lines = extract_lines(test_file, 1, count=10)
        print(lines)
        print()
        
        # 测试文本搜索
        print("3. 测试文本搜索 (搜索'trace'):")
        search_result = search_text(test_file, "trace", context=2)
        print(search_result)
        print()
        
        # 测试加密魔数搜索
        print("4. 测试加密魔数搜索:")
        crypto_result = search_crypto_magic(test_file)
        print(crypto_result)
        print()
        
        print("✅ 所有测试完成!")
        
    except LargeTextSearcherError as e:
        print(f"❌ Skill错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")


if __name__ == "__main__":
    test_skill_functions()