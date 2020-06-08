# AutoLogin
自动登录东南大学每日打卡报平安

这是一个自动每日报平安打卡的python脚本，基于Selenium库

## Compilation

如果您想自己编译python代码，则需要：

* python3
* 安装selenium库
* 与浏览器对应的Webdriver

## Usage

请直接点击exe文件运行程序，第一次运行需要输入您的一卡通号和密码（这完全保存在您的计算机上，并不会泄露给我或其他人）。

如果您每晚都需要关闭计算机，建议将exe文件的快捷方式添加到开机启动目录，这样在您第二天打开计算机的时候便可以自动运行程序。

其主要实现的功能有：

* 第一次登录成功后密码保存在本地，以后再次运行无需重复输入密码
* 每日10点钟之前自动打卡，具体打卡时间与第一次登录时间有关
* 打卡成功后会在log中记录打卡的时间方便查看，如果愿意的话可以接入微信报备（可以但没必要，鉴于该功能并不一定适用所有人，如果您需要请单独联系开发者）

## Configuration

Chrome版需要的配置有：

* 最新版本的64位Chrome浏览器（必须，版本号为83.0.4103.97）

Edge版需要的配置有：

* 最新版Chromium内核的64位Edge浏览器（必须，版本号为83.0.478.45）
* 请务必确认Edge浏览器的缩放比例为100%
* Edge浏览器无法后台静默运行，也无法隐藏log，因而为了极致使用体验还是建议使用Chrome

IE版需要的配置有（IE同样无法后台静默运行，开发计划无限搁浅）：

* 最新版IE浏览器（必须）
* 请务必保证IE浏览器的缩放比例为100%，工具-缩放请务必选择100%，建议提前打开IE浏览器查看缩放比例
* 请务必关闭IE保护模式，请前往工具-Internet选项-安全，将Internet，本地Internet，受信任的站点，受限制的站点这四个区域的下方方框——启用保护模式（要求重新启动Internet Explorer）前面的勾都去掉，然后点击确认并重启浏览器确认这四个区域的保护模式都已经关闭
* 建议将seu.edu.cn加入到IE的兼容性视图，兼容性视图设置在工具-兼容性视图设置

## Warning

* 请不要随便升级浏览器，否则需要重新下载webdriver并自行替换

   Edge Webdriver 下载地址：https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

   Chrome Webdriver 下载地址：http://chromedriver.storage.googleapis.com/index.html

* 如果第一次您的密码输入错误，请自行寻找loginData.txt文档并修改成正确的账号密码

