#!/usr/bin/env python3
"""MCP服务器功能测试脚本"""

import asyncio


async def main():
    """显示MCP服务器信息"""
    print("=== Large Text Searcher MCP Server ===\n")
    
    tools = [
        ("generate_random_number", "生成随机数"),
        ("file_info", "获取文件基本信息"),
        ("extract_lines", "提取文件指定行"),
        ("search_text", "在文件中搜索文本")
    ]
    
    print("可用工具:")
    for name, desc in tools:
        print(f"  • {name}: {desc}")
    
    print(f"\n配置文件: .kiro/settings/mcp.json")
    print("启动服务器: python random_number_mcp.py")
    print("在Kiro中使用这些工具进行大文件分析和搜索")


if __name__ == "__main__":
    asyncio.run(main())