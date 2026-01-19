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


