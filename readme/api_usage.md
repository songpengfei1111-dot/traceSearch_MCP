# 命令行使用指南

这个文档展示了如何使用large-text-viewer的命令行功能，这些功能复用了GUI版本的核心组件，但提供了无需前端渲染的高性能文本处理能力。


## 命令行功能

### 1. 文件信息 (info)

显示文件的基本信息，如大小、行数等。

```bash

# 基本文件信息
./target/release/large-text-viewer info --file /Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_XG.txt
```

输出示例：
```
File: /Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_XG.txt
Size: 14794093 bytes
Lines: 254800
```

### 2. 行提取 (lines)

从文件中提取指定范围的行，支持大文件的高效随机访问。

```bash
# 提取第1-100行
./target/release/large-text-viewer lines --file /Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_XG.txt --start 1 --end 100

# 从第1000行开始提取50行
./target/release/large-text-viewer lines --file /Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_XG.txt --start 1000 --count 50

# 显示行号 (默认使用这个)
./target/release/large-text-viewer lines --file  /Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_XG.txt  --start 1 --count 10 --line-numbers

# 提取单行
./target/release/large-text-viewer lines --file /path/to/large.txt --start 42 --count 1
```

### 3. 文本搜索 (search)

在大文件中进行高性能搜索，支持正则表达式和并行处理。

```bash
# 基本文本搜索
./target/release/large-text-viewer search --file /Users/teng/PycharmProjects/pythonProject/shopee_proj/log/record_00.txt --pattern "string" --max-results 50000 
--count-only

# 正则表达式搜索
./target/release/large-text-viewer search --file /path/to/large.txt --pattern "\d{4}-\d{2}-\d{2}" --regex

# 区分大小写搜索
./target/release/large-text-viewer search --file /path/to/large.txt --pattern "Error" --case-sensitive

# 只统计匹配数量
./target/release/large-text-viewer search --file /path/to/large.txt --pattern "error" --count-only

# 限制结果数量
./target/release/large-text-viewer search --file /path/to/large.txt --pattern "error" --max-results 50

# 显示上下文行
./target/release/large-text-viewer search --file /path/to/large.txt --pattern "error" --context 3
```

搜索输出示例：
```
    1042: This is an error message
>   1043: Following line
--
    2156: Another error occurred
    2157: Stack trace follows
>   2158: at function xyz()

Showed 2 matches
```


//TODO 限制总行数，而不是结果的数量
//有些事情就在mcp-api层面限制死，不需要总让ai来注意
//先提供一些通过魔数获取的算法先验，或者你已经分析了一半的结论
//提供一段基于文字描述的trace段虚拟内存

|line1-line2000:0xaaaa-0xbbbb:描述|
//搜索结果多的时候要如何让ai能注意到关键的信息，比如一大段结果， 我们可以通过memset 0 或者malloc 知道这是在初始化这段内存，所以写入这段内存的逻辑一定在初始化内存和最终的结果之间，这个逻辑要如何告诉ai
//在trace引擎中提供
//core增添har包解析，csv解析功能，对于格式确定的东西，用rust版pandas会更快吧
//或者...这些工作为什么要手搓呢，我是说，只要在mcp里提供这些功能就行了，肯定已经有人的规则引擎已经做的更好了。trace搜索这块的后段也是换成rigrep，grep也行，python mcp只要提供命令行中转就可以了
//不要为了做而做

