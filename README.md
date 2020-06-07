# AutoLogin
自动登录东南大学每日打卡报平安

这是一个自动每日报平安打卡的python脚本，请直接点击login1.0.exe运行程序，第一次运行需要输入您的一卡通号和密码（这完全保存在您的计算机上，并不会泄露给我或其他人）。其主要实现的功能有：

* 第一次登录成功后密码保存在本地，以后再次运行无需重复输入密码
* 每日10点钟之前自动打卡，具体打卡时间与第一次登录时间有关
* 打卡成功后会在log中记录打卡的时间方便查看，如果愿意的话可以接入微信报备（可以但没必要）


Chrome版需要的配置有：

* 最新版本的Chrome浏览器（必须，版本号为83.0.4103.97）

Edge版需要的配置有：

* 最新版Chromium内核的Edge浏览器（必须）
* 请务必确认Edge浏览器的缩放比例为100%
* Edge浏览器无法后台静默运行，也无法隐藏log，因而为了极致使用体验还是建议使用Chrome

NOTE：

* 请不要随便升级浏览器，否则需要重新下载webdriver并自行替换
   Edge Webdriver 下载地址：https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
   Chrome Webdriver 下载地址：http://chromedriver.storage.googleapis.com/index.html
* 如果第一次您的密码输入错误，请自行寻找loginData.txt文档并修改成正确的账号密码
