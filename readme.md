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
840480a30000267b86a1b0f7e6814449319585f86[record_00 2.txt.zip](../pythonProject/shopee_proj/log/record_00%202.txt.zip)f7f2056e72f 中 267b86a1b0f7e6814449319585f86f7f2056e72f 的生成算法

//TODO context 提供小范围的反向污点，增加context质量
//升级后段，给search_text增添行范围筛选
//增加书签功能，让模型能标记某某行到某某行是什么作用，把一些范围标记为没用，并影响筛选结果
//告诉ai哪些搜索方案是不严谨的
{
  "context": 5,
  "file_path": "/Users/teng/PycharmProjects/pythonProject/shopee_proj/log/record_00.txt",
  "max_results": 10,
  "pattern": "704da53700"
}
比如这种搜索结果极其容易导致偏见，max_results可以不给ai操作，ai只能获取结果
这样的话或许可以给find_prev和find_next? 这样的话就又回到污点上了

//ai本身智力发挥占很大一部分，菜的ai只会死找，厉害的能从明文开始猜测正反向同时推，也知道利用memcpy等信息
//添加一些辅助功能，比如魔数搜索，让模型知道某些地方有加密算法，或者先枚举所有出现过的libc函数，让ai有整体印象
//提供ida mcp 让模型能靠反编译代码获取局部信息
//添加unidbg mcp 让模型能通过unidbg分析算法模拟
//看起来确实有必要在python层限制ai的自由发挥，有些参数不应该给他用，会导致偏激的思路
//在mcp给ai的返回中也可以给出提示，比如进行计数，10次搜索以后提醒ai该总结了

[+] 新功能：搜索结果溢出100个时结果已经没有意义，直接在mcp拦截，让模型重新思考如何搜索，不要浪费token还把结果看一遍

//不同的模型在使用api上有不同的偏好，claude更喜欢使用context，而gemini更喜欢使用正则匹配，但都不太喜欢搜指令 add a,c,b 这样的
