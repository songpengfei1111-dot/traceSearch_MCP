#!/usr/bin/env python3
"""Large Text Searcher Skill - 为Trae提供大文件搜索功能"""

import os
import subprocess
from typing import Any, Dict, List, Optional

from crypto_magic_search import search_all_crypto_magic, format_search_results

# 常量定义
EXECUTABLE_PATH = "./target/release/large-text-viewer"


class LargeTextSearcherError(Exception):
    """大文件搜索器异常"""
    pass


def _check_executable() -> bool:
    """检查可执行文件是否存在"""
    return os.path.exists(EXECUTABLE_PATH)


def _run_command(cmd: List[str]) -> str:
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
                match_count = int((match or match1).group(1))
                if match_count >= 100:  # 当显示100个结果时，说明可能有更多结果被截断
                    raise LargeTextSearcherError("返回结果过多，请重新考虑搜索规则，比如考虑给出搜索的行数限制")
                
        return output
    except subprocess.CalledProcessError as e:
        raise LargeTextSearcherError(e.stderr or "命令执行失败")
    except Exception as e:
        raise LargeTextSearcherError(str(e))


def get_file_info(file_path: str) -> str:
    """获取文件的基本信息，如大小、行数等
    
    Args:
        file_path: 要查询信息的文件路径
        
    Returns:
        包含文件信息的字符串
        
    Raises:
        LargeTextSearcherError: 当操作失败时
    """
    if not file_path:
        raise LargeTextSearcherError("需要提供file_path参数")
    
    if not _check_executable():
        raise LargeTextSearcherError(f"找不到可执行文件 {EXECUTABLE_PATH}，请先编译项目")
    
    cmd = [EXECUTABLE_PATH, "info", "--file", file_path]
    return _run_command(cmd)


def extract_lines(
    file_path: str, 
    start: int, 
    end: Optional[int] = None, 
    count: Optional[int] = None, 
    line_numbers: bool = True
) -> str:
    """从文件中提取指定范围的行，支持大文件的高效随机访问
    
    Args:
        file_path: 文件路径
        start: 起始行号
        end: 结束行号（可选）
        count: 要提取的行数（可选）
        line_numbers: 是否显示行号（默认True）
        
    Returns:
        提取的行内容
        
    Raises:
        LargeTextSearcherError: 当操作失败时
    """
    if not file_path or start is None:
        raise LargeTextSearcherError("需要提供file_path和start参数")
    
    if not _check_executable():
        raise LargeTextSearcherError(f"找不到可执行文件 {EXECUTABLE_PATH}，请先编译项目")
    
    # 构建命令参数
    cmd = [EXECUTABLE_PATH, "lines", "--file", file_path, "--start", str(start)]
    
    if end is not None:
        cmd.extend(["--end", str(end)])
    elif count is not None:
        cmd.extend(["--count", str(count)])
    
    if line_numbers:
        cmd.append("--line-numbers")
    
    return _run_command(cmd)


def search_text(
    file_path: str, 
    pattern: str, 
    context: int = 0, 
    regex: bool = False
) -> str:
    """在大文件中进行高性能搜索，支持正则表达式和并行处理
    
    Args:
        file_path: 文件路径
        pattern: 搜索模式，不仅仅可以搜索关键词，也可以搜索关键的汇编指令
        context: 为搜索结果提供几行上下文(更多的信息，适合与关键词搜索配合使用)
        regex: 是否使用正则表达式（默认False）使用正则一定要设为True
        
    Returns:
        搜索结果
        
    Raises:
        LargeTextSearcherError: 当操作失败时
    """
    if not file_path or not pattern:
        raise LargeTextSearcherError("需要提供file_path和pattern参数")
    
    if not _check_executable():
        raise LargeTextSearcherError(f"找不到可执行文件 {EXECUTABLE_PATH}，请先编译项目")
    
    # 构建命令参数
    cmd = [EXECUTABLE_PATH, "search", "--file", file_path, "--pattern", pattern]
    
    # 添加可选参数
    if regex:
        cmd.append("--regex")
    
    if context > 0:
        cmd.extend(["--context", str(context)])
    
    return _run_command(cmd)


def search_crypto_magic(file_path: str) -> str:
    """通过搜索文件中的加密算法魔数，定位加密算法并找到入参
    
    Args:
        file_path: 要搜索的文件路径
        
    Returns:
        格式化的搜索结果
        
    Raises:
        LargeTextSearcherError: 当操作失败时
    """
    if not file_path:
        raise LargeTextSearcherError("需要提供file_path参数")

    if not _check_executable():
        raise LargeTextSearcherError(f"找不到可执行文件 {EXECUTABLE_PATH}，请先编译项目")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise LargeTextSearcherError(f"文件不存在: {file_path}")

    try:
        results = search_all_crypto_magic(file_path)
        # 根据参数选择格式化函数
        formatted_result = format_search_results(results)
        return formatted_result
        
    except Exception as e:
        raise LargeTextSearcherError(f"搜索过程中发生错误: {str(e)}")


# 为了保持向后兼容性，提供一些别名函数
def file_info(file_path: str) -> str:
    """获取文件信息的别名函数"""
    return get_file_info(file_path)


# 导出所有公共函数
__all__ = [
    # 'get_file_info',
    'extract_lines', 
    'search_text',
    'search_crypto_magic',
    'file_info',
    # 'LargeTextSearcherError'
]