# MCP到Skill迁移指南

本文档说明如何从MCP服务器模式迁移到Trae Skill模式。

## 迁移概述

原来的`large_text_viewer_mcp.py`已经被转换为Trae skill格式，位于`.trae/skills/large-text-searcher/`目录下。

## 主要变化

### 1. 项目结构变化

**之前 (MCP模式):**
```
├── large_text_viewer_mcp.py    # MCP服务器主文件
├── crypto_magic_search.py      # 加密魔数搜索
├── readme.md                   # 项目说明
└── readme/                     # 文档目录
    ├── api_usage.md
    ├── search_strategy.md
    └── trace_format.md
```

**现在 (Skill模式):**
```
├── .trae/skills/large-text-searcher/
│   ├── SKILL.md                # Skill描述文件
│   ├── __init__.py             # Python包初始化
│   ├── large_text_searcher.py  # 主要功能实现
│   ├── crypto_magic_search.py  # 加密魔数搜索
│   ├── test_skill.py           # 测试脚本
│   ├── README.md               # 使用说明
│   └── docs/                   # 文档目录
│       ├── api_usage.md
│       ├── search_strategy.md
│       └── trace_format.md
├── large_text_viewer_mcp.py    # 保留原文件
└── readme.md                   # 项目说明
```

### 2. 使用方式变化

**之前 (MCP模式):**
```bash
# 启动MCP服务器
python large_text_viewer_mcp.py

# 在Kiro中配置MCP服务器
# 通过MCP协议调用工具
```

**现在 (Skill模式):**
```python
# 直接导入使用
from .trae.skills.large_text_searcher import (
    get_file_info,
    extract_lines,
    search_text,
    search_crypto_magic
)

# 或者在Trae中直接使用，skill会自动加载
```

### 3. API变化

核心功能保持不变，但调用方式有所简化：

| MCP工具名 | Skill函数名 | 说明 |
|-----------|-------------|------|
| `file_info` | `get_file_info()` | 获取文件信息 |
| `extract_lines` | `extract_lines()` | 提取指定行 |
| `search_text` | `search_text()` | 文本搜索 |
| `search_crypto_magic` | `search_crypto_magic()` | 加密魔数搜索 |

### 4. 错误处理变化

**之前 (MCP模式):**
```python
# 返回TextContent列表
return [TextContent(type="text", text=f"错误: {message}")]
```

**现在 (Skill模式):**
```python
# 抛出自定义异常
raise LargeTextSearcherError(f"错误: {message}")
```

## 迁移步骤

### 1. 确保依赖满足
- Rust后端程序已编译：`cargo build --release`
- 可执行文件位于：`./target/release/large-text-viewer`

### 2. 测试Skill功能
```bash
cd .trae/skills/large-text-searcher/
python test_skill.py
```

### 3. 在Trae中使用
Skill会自动被Trae发现和加载，你可以直接在对话中使用相关功能。

### 4. 更新现有脚本（如果有）
如果你有使用MCP客户端的脚本，需要更新为直接导入skill模块的方式。

## 优势

### Skill模式的优势：
1. **更简单的部署**：无需启动独立的MCP服务器进程
2. **更好的集成**：与Trae深度集成，使用更自然
3. **更高的性能**：减少了进程间通信开销
4. **更容易调试**：可以直接在Python中调试
5. **更好的错误处理**：使用Python异常机制

### 保留的功能：
- 所有核心搜索功能完全保留
- 加密算法魔数识别功能保留
- 智能结果控制机制保留
- 高性能Rust后端保留

## 兼容性

- 原有的MCP文件仍然保留，可以继续使用
- 新的Skill模式与原有功能完全兼容
- 可以根据需要选择使用MCP模式或Skill模式

## 故障排除

### 常见问题：

1. **找不到可执行文件**
   ```
   错误: 找不到可执行文件 ./target/release/large-text-viewer，请先编译项目
   ```
   解决：运行 `cargo build --release`

2. **Skill未被识别**
   - 确保`.trae/skills/large-text-searcher/SKILL.md`文件存在
   - 检查SKILL.md文件的YAML前置元数据格式是否正确

3. **导入错误**
   - 确保`__init__.py`文件存在
   - 检查Python路径设置

## 技术支持

如果在迁移过程中遇到问题，可以：
1. 查看测试脚本的输出
2. 检查Trae的日志
3. 参考文档目录下的详细说明