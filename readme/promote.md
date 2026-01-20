使用mcp，large-text-searcher： 






使用large-text-viewer-mcp：
先阅读 readme 中的 trace_format.md 和 search_strategy.md 了解trace格式和搜索策略
任务:
找出"x-sap-ri": 的值是如何生成的
提示:
你可以用开头的4位或8位定位，由于是要找最开始生成的逻辑，所以你可以从最开始出现的地方开始找




使用large-text-viewer-mcp： 
先阅读 readme 中的 trace_format.md 和 search_strategy.md 了解trace格式和搜索策略
任务：
找出/Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_tk.txt 文件中
08d2a4808204100218f283aa9c01220431323333320...
这一段protobuf的生成逻辑。
提示：
你可以用开头的 08d2a480 作为定位符号，告诉我是生产这段的线索



使用large-text-viewer-mcp： 
 阅读my_XL.py 文件，在其中有一个 randomBytes = bytes.fromhex('c62cbe67') ，每次都不一样，请根据其他的关键明文定位找出在 
 /Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_tk.txt 中，这个对应的随机randomBytes应该是多少


使用large-text-viewer-mcp：
先阅读 readme 中的 trace_format.md 和 search_strategy.md 了解trace格式和搜索策略
然后阅读 argus.py, 了解算法逻辑
任务:
argus 中sm3的输入是
bytearray(base64.b64decode(base64Key) + bytes.fromhex(randomNum1 + randomNum2) + base64.b64decode(base64Key))
我需要你找出 randomNum1 和 randomNum2 这两个随机数在 /Users/teng/PycharmProjects/pythonProject/tiktok/log/record_00_tk.txt 中对应的值
提示:
请根据其他的关键明文的线索定位找出其值 可以通过base64Key会与其拼接这个关键特征进行定位
base64Key = 'wC8lD4bMTxmNVwY5jSkqi3QWmrphr/58ugLko7UZgWM='


使用large-text-viewer-mcp：
先阅读 readme 中的 trace_format.md 和 search_strategy.md 了解trace格式和搜索策略
然后阅读 argus.py, 了解算法逻辑
任务:
在 argus.py 的计算逻辑中
reversedNewStr = reversedStr+'0000000000008000'
其中 reversedStr 每8位一存储，我需要验证这里reversedStr后拼接的是否还是0000000000008000
提示:
reversedStr 最后的部分是 7662bc00f93b6c57 可以通过这个值来找内存地址，然后定位到 0000000000008000 或者替代 0000000000008000 的值


