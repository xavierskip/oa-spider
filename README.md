# oa spider

一个定制的下载办公OA系统上文件的爬虫。

基于python3.


`oa-spider.py` 主要用来连接ssl-vpn，做好登录网站的准备，利用`psutil`库来记录进程的pid，避免重复连接vpn,进程的pid信息保存在当前路径`pids`文件里。准备好网络连接后，最后一部分
``` python
from oa_spider.run import main
from oa_spider import OAini

main(OAini)
```
用来启动爬虫。

执行 `python -m oa_spider` 可以单独用来运行爬虫部分不涉及vpn网络的连接。

代码仅供交流学习使用。