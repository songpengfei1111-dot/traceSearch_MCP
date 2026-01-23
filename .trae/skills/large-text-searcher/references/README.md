# Large Text Searcher Skill

这是一个专门用于处理大规模文本文件的高性能搜索与分析skill，从原来的MCP服务器转换而来。

## 功能特性

- **高效文件信息获取**：快速获取大文件的基本信息（大小、行数等）
- **精准行提取**：支持大文件的高效随机行访问
- **强大搜索功能**：支持关键词搜索、正则表达式匹配
- **加密算法识别**：通过魔数自动识别文件中的加密算法
- **智能结果控制**：自动检测搜索结果数量，防止信息过载

## 安装要求

1. 需要编译Rust后端程序：
   ```bash
   cargo build --release
   ```

2. 确保可执行文件位于 `./target/release/large-text-viewer`

## 使用方法

### 在Python中使用

```python
from large_text_searcher import (
    get_file_info,
    extract_lines,
    search_text,
    search_crypto_magic,
    LargeTextSearcherError
)

try:
    # 获取文件信息
    info = get_file_info("path/to/large_file.txt")
    print(info)
    
    # 提取指定行
    lines = extract_lines("path/to/large_file.txt", start=100, count=20)
    print(lines)
    
    # 搜索文本
    results = search_text("path/to/large_file.txt", "search_pattern", context=5)
    print(results)
    
    # 搜索加密算法魔数
    crypto_results = search_crypto_magic("path/to/large_file.txt")
    print(crypto_results)
    
except LargeTextSearcherError as e:
    print(f"错误: {e}")
```

### 在Trae中使用

这个skill会自动被Trae识别并加载，你可以直接在对话中使用相关功能。

## API参考

### get_file_info(file_path: str) -> str
获取文件的基本信息，如大小、行数等。

### extract_lines(file_path: str, start: int, end: Optional[int] = None, count: Optional[int] = None, line_numbers: bool = True) -> str
从文件中提取指定范围的行。

### search_text(file_path: str, pattern: str, context: int = 0, regex: bool = False) -> str
在大文件中进行高性能搜索。

### search_crypto_magic(file_path: str) -> str
通过搜索文件中的加密算法魔数，定位加密算法并找到入参。

## 文档

- [搜索策略指南](search_strategy.md) - ARM64逆向分析的搜索策略
- [Trace格式说明](trace_format.md) - 汇编指令trace文件格式解释

## 测试

运行测试脚本：
```bash
python test_skill.py
```