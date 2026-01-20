# 基于large-text-viewer的 trace分析mcp

文本搜索后端可以按你的喜好更换，比如rigrep甚至直接命令行grep

目前在kiro上使用

search_strategy.md 和 trace_format.md 要使用你自己的trace格式

⚠️注意⚠️
ai的大脑褶皱是平滑的，你只能让他代替你进行机械化的劳动，或者期待他某一下灵光一闪

所以，流水化和标准化的trace搜索方法是你要考虑的，ai做不了你自己认知以外的事

简单的算法ai表现很好，但复杂一些的算法会大量烧token，且表现不一定好，这里要自己多调试

技术交流可以加 vx baserker2 加好备注

测试mcp

阅读 readme/中 trace_format.md 和 search_strategy.md 的要求
通过mcp分析/Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_XG.txt 中
840480a30000267b86a1b0f7e6814449319585f86f7f2056e72f 中 267b86a1b0f7e6814449319585f86f7f2056e72f 的生成算法

//TODO context 提供小范围的反向污点，增加context质量
//升级后段，给search_text增添行范围筛选
//增加书签功能，让模型能标记某某行到某某行是什么作用，把一些范围标记为没用，并影响筛选结果
//todo，添加一些辅助功能，不如魔数搜索，让模型知道某些地方有加密算法
//提供ida mcp 让模型能靠反编译代码获取局部信息
//添加unidbg mcp 让模型能通过unidbg分析算法模拟

[+] 新功能：搜索结果溢出100个时结果已经没有意义，直接在mcp拦截，让模型重新思考如何搜索，不要浪费token还把结果看一遍


