#!/usr/bin/env python3
"""Large Text Searcher MCP Server - 为Kiro提供大文件搜索功能"""

import asyncio
import os
import re
import random
import subprocess
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 常量定义
EXECUTABLE_PATH = "./target/release/large-text-viewer"
SERVER_NAME = "largeTextSearcher-server"

server = Server(SERVER_NAME)


def _create_error_response(message: str) -> List[TextContent]:
    """创建错误响应"""
    return [TextContent(type="text", text=f"错误: {message}")]


def _create_success_response(text: str) -> List[TextContent]:
    """创建成功响应"""
    return [TextContent(type="text", text=text)]


def _check_executable() -> bool:
    """检查可执行文件是否存在"""
    return os.path.exists(EXECUTABLE_PATH)


def _run_command(cmd: List[str]) -> List[TextContent]:
    """执行命令并返回结果"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # 检查搜索结果数量
        output = result.stdout
        if "matches" in output:
            import re
            # 匹配 "Showed xxx matches" 模式
            match = re.search(r'Showed\s+(\d+)\s+matches', output)
            match1 = re.search(r'Found\s+(\d+)\s+matches', output)
            if match or match1:
                match_count = int(match.group(1))
                if match_count >= 100:  # 当显示100个结果时，说明可能有更多结果被截断
                    return _create_error_response("返回结果过多，请重新考虑搜索规则，比如考虑给出搜索的行数限制")
                
        return _create_success_response(output)
    except subprocess.CalledProcessError as e:
        return _create_error_response(e.stderr or "命令执行失败")
    except Exception as e:
        return _create_error_response(str(e))

@server.list_tools()
async def list_tools() -> List[Tool]:
    """定义可用的工具列表"""
    return [
        Tool(
            name="generate_random_number",
            description="生成一个随机数",
            inputSchema={
                "type": "object",
                "properties": {
                    "min": {"type": "integer", "description": "最小值（默认为1）"},
                    "max": {"type": "integer", "description": "最大值（默认为100）"}
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="file_info",
            description="获取文件的基本信息，如大小、行数等",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要查询信息的文件路径"}
                },
                "required": ["file_path"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="extract_lines",
            description="从文件中提取指定范围的行，支持大文件的高效随机访问",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "start": {"type": "integer", "description": "起始行号"},
                    "end": {"type": "integer", "description": "结束行号（可选）"},
                    "count": {"type": "integer", "description": "要提取的行数（可选）"},
                    "line_numbers": {"type": "boolean", "description": "是否显示行号（默认true）"}
                },
                "required": ["file_path", "start"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="search_text",
            description="在大文件中进行高性能搜索，支持正则表达式和并行处理",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "pattern": {"type": "string", "description": "搜索模式，不仅仅可以搜索关键词，也可以搜索关键的汇编指令，如果需要结果的上下文，考虑同时使用context"},
                    "regex": {"type": "boolean", "description": "是否使用正则表达式（默认false）"},
                    # "case_sensitive": {"type": "boolean", "description": "是否区分大小写（默认false）"},
                    # "count_only": {"type": "boolean", "description": "是否只统计匹配数量（默认false）"},
                    # "max_results": {"type": "integer", "description": "最大结果数量（默认50）"},
                    "context": {"type": "integer", "description": "显示上下文行数（默认0）从目标行向上n行为上下文"}
                },
                "required": ["file_path", "pattern"],
                "additionalProperties": False
            }
        )
    ]


def _handle_random_number(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理随机数生成"""
    min_val = arguments.get("min", 1)
    max_val = arguments.get("max", 100)
    
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    
    random_num = random.randint(min_val, max_val)
    return _create_success_response(f"生成的随机数: {random_num} (范围: {min_val}-{max_val})")


def _handle_file_info(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理文件信息查询"""
    file_path = arguments.get("file_path")
    if not file_path:
        return _create_error_response("需要提供file_path参数")
    
    if not _check_executable():
        return _create_error_response(f"找不到可执行文件 {EXECUTABLE_PATH}，请先编译项目")
    
    cmd = [EXECUTABLE_PATH, "info", "--file", file_path]
    return _run_command(cmd)


def _handle_extract_lines(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理行提取"""
    file_path = arguments.get("file_path")
    start = arguments.get("start")
    
    if not file_path or start is None:
        return _create_error_response("需要提供file_path和start参数")
    
    if not _check_executable():
        return _create_error_response(f"找不到可执行文件 {EXECUTABLE_PATH}，请先编译项目")
    
    # 构建命令参数
    cmd = [EXECUTABLE_PATH, "lines", "--file", file_path, "--start", str(start)]
    
    end = arguments.get("end")
    count = arguments.get("count")
    line_numbers = arguments.get("line_numbers", True)
    
    if end is not None:
        cmd.extend(["--end", str(end)])
    elif count is not None:
        cmd.extend(["--count", str(count)])
    
    if line_numbers:
        cmd.append("--line-numbers")
    
    return _run_command(cmd)


def _handle_search_text(arguments: Dict[str, Any]) -> List[TextContent]:
    """处理文本搜索"""
    file_path = arguments.get("file_path")
    pattern = arguments.get("pattern")
    
    if not file_path or not pattern:
        return _create_error_response("需要提供file_path和pattern参数")
    
    if not _check_executable():
        return _create_error_response(f"找不到可执行文件 {EXECUTABLE_PATH}，请先编译项目")
    
    # 构建命令参数
    cmd = [EXECUTABLE_PATH, "search", "--file", file_path, "--pattern", pattern]
    
    # 添加可选参数
    if arguments.get("regex", False):
        cmd.append("--regex")
    if arguments.get("case_sensitive", False):
        cmd.append("--case-sensitive")
    if arguments.get("count_only", False):
        cmd.append("--count-only")
    
    max_results = arguments.get("max_results", 50)
    if max_results != 50:
        cmd.extend(["--max-results", str(max_results)])
    
    context = arguments.get("context", 0)
    if context > 0:
        cmd.extend(["--context", str(context)])
    
    return _run_command(cmd)


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """工具调用分发器"""
    handlers = {
        "generate_random_number": _handle_random_number,
        "file_info": _handle_file_info,
        "extract_lines": _handle_extract_lines,
        "search_text": _handle_search_text,
    }
    handler = handlers.get(name)
    if not handler:
        raise ValueError(f"未知工具: {name}")
    return handler(arguments)


async def main():
    """启动MCP服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())