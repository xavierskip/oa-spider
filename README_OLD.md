# oa spider

下载电子公文网站文件的自动化爬虫工具。

目前基于 Python2.7。依赖 requests Pillow pyquery 库。 

目前支持的网站
1. 荆州市卫计委
2. 湖北省疾控中心
3. 湖北省卫计委（需要 VPN 连接）

## 使用方法

下载或者`git clone`到本地。

`pip install -r requirements.txt`安装依赖库。

(Debian 系 Linux 系统安装 pyquery 之前需要安装依赖`sudo apt-get install libxml2-dev libxslt1-dev python-dev`)

以目录下的`oa.ini.example`文件的内容为模板修改或者新建配置文件`oa.ini`。

`python run.py` 

(注意：在Windows平台下暂不支持在中文文件路径下运行)

**为了配合本工具使用以及其他功能以达到及时自动下载新公文到电脑上的目的，本工具需要一些其他系统功能、组件配合使用。**

（以下*Linux*环境皆以*Ubuntu*为例）

#### 定时执行

**Linux**

crontab 配置([crontab.guru](https://crontab.guru/)一个让 crontab 说人话的网站)
    
    # 定时抓取
    >: crontab -e
    1,21,41 8-18 * * * /the/path/to/run.py >> /tmp/oa_run.log 2>&1
    # VPN 连接
    >: sudo crontab -e
    PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
    0,20,40 8-18 * * * /the/path/to/vpn.sh

**windows**

配置计划任务。在 Windows XP 下消除运行弹出的黑框需要改变运行用户为`NT AUTHORITY\SYSTEM`

#### 同步文件

当工具运行设备和最终使用设备不是同一台电脑时候，我们需要同步下载的文件到目标电脑，我使用[seafile](http://seafile.com/)同步文件到目标电脑中。

我以部署到树莓派为例。

##### 服务端

需要安装`sudo apt-get install sqlite3`

[下载 raspberry pi 版本](https://github.com/haiwen/seafile-rpi/releases)

[根据文档进行安装](https://manual-cn.seafile.com/deploy/using_sqlite.html)

[设置开机启动服务](https://manual-cn.seafile.com/deploy/start_seafile_at_system_bootup.html)

[开启 WebDAV扩展](https://manual-cn.seafile.com/extension/webdav.html)

##### 客户端

安装:[Seafile Client for Raspberry Pi](https://github.com/saljut7/seafile-client-rpi)

配置:[Seafile-cli-manual](https://seacloud.cc/group/3/wiki/seafile-cli-manual)

客户端开机启动:
修改`/etc/rc.local`文件,增加`sudo -u <username> seaf-cli start`

#### 邮件通知

**Linux**

`sudo apt-get install mutt msmtp` 安装

创建文件`~/.muttrc`

    set sendmail="/usr/bin/msmtp"
    set use_from=yes
    set realname="OA spider"
    set from=yourmail@mail.com
    set envelope_from=yes
    set charset="utf-8"
    set send_charset="utf-8"
    set locale = "zh_CN.UTF-8"
    set content_type = "text/html\;charset=utf-8”
    
创建文件`~/.msmtprc`

    account default
    host smtp.163.com 
    from yourmail@mail.com  
    auth login                           
    user yourmail@mail.com
    password yourmailpasswd            
    logfile /tmp/msmtp.log

`chmod 400 ~/.msmtprc`修改文件权限

发送

    mutt -s "主题" to@163.com -a 附件.txt < mail.txt

发送多个

    MailList=`cat list.txt`
    mutt -s "主题" $MailList -a 附件1 -a 附件2  < mail.txt
    
**Windows**

todo: python 直接发送邮件


#### 湖北卫计委 VPN 连接配置

**Linux**

安装`sudo apt-get install pptp-linux`

配置`pptpsetup -create hbwjw -server 219.140.56.98 -username <username> -password <passwd> -encrypt`

增加静态路由

新建文件`sudo vim /etc/ppp/ip-up.d/hbwjw_route`

    #!/bin/bash
    /sbin/route add 192.168.20.190 dev ppp0

增加文件执行权限`sudo chmod +x /etc/ppp/ip-up.d/hbwjw_route`

连接`sudo pon hbwjw`

断开`sudo poff hbwjw`

todo:
 * pon without sudo? `Error: only members of the 'dip' group can use this command.`
 * 连接5分钟掉线? `LCP terminated by peer (MPPE disabled)`

**Windows**

手动连接 VPN