# AutoLogin

[![license](https://img.shields.io/github/license/StephenHoo/AutoLogin)](https://github.com/StephenHoo/AutoLogin/blob/master/LICENSE)
[![Release Version](https://img.shields.io/github/release/StephenHoo/AutoLogin)](https://github.com/StephenHoo/AutoLogin/releases)

自动登录东南大学每日打卡报平安

这是一个自动每日报平安打卡的python脚本，基于Selenium库

团队打卡版本可以请访问 [typex.ltd](https://www.typex.ltd)，之前承诺的功能应该都做到了。

## Compile

如果您想自己编译python代码，则需要：

* python3
* 安装selenium库
* 与浏览器对应的Webdriver

## Usage

前往 [releases](https://github.com/StephenHoo/AutoLogin/releases) 下载最新版本安装包并解压。

请直接点击exe文件运行程序，第一次运行需要输入您的**一卡通号**和**密码**（这完全保存在您的计算机上，并不会泄露给我或其他人）。

如果您每晚都需要关闭计算机，建议将exe文件的**快捷方式**添加到开机启动目录，这样在您第二天打开计算机的时候便可以自动运行程序。

其主要实现的功能有：

* 第一次登录成功后密码保存在本地，以后再次运行无需重复输入密码
* 每日10点钟之前自动打卡，具体打卡时间与第一次登录时间有关
* 打卡成功后会在log中记录打卡的时间方便查看，如果愿意的话可以接入微信报备（可以但没必要，鉴于该功能并不一定适用所有人，如果您需要请单独联系开发者）

**1.3 版本更新，在打卡之后可以自动开始第二日入校申请**

* 默认兼容1.2版本，只有将 loginData.json 文件（loginData.json 文件会在程序第一次运行之后自动生成）中的 destination 手动改为改为具体的"所到楼宇"才会激活第二日入校申请（此时需要重新启动程序配置才会生效）
参考格式：{"username": "1111111", "password": "ABABABABABAB", "loc": "", "destination": "教务处380"}
* 1.3版本目前默认的”申请理由“为”到办公室科研“，如需要选择其他选项，请手动更改源码或等待后续更新（咕咕咕）
* 1.3版本默认的通行开始时间为8：31，结束时间为20：31，如需要选择其他选项，请手动更改源码或等待后续更新（咕咕咕）
* 1.3版本测试的通行区域为”四牌楼校区“，不保证其他校区的同学也可以正常使用
* 1.3版本目前仅有 Chrome 版，如使用的是其他浏览器，请手动更改源码或等待后续更新（咕咕咕）

程序正常运行的界面截图：

![dbiQqH.png](https://s1.ax1x.com/2020/08/30/dbiQqH.png)


## Configuration

### Chrome 版需要的配置有：

* 最新版本的64位 Chrome 浏览器（必须，版本号为 83.0.4103.97，请前往 [Chrome官网](https://www.google.cn/intl/zh-CN/chrome/) 进行下载)
* **最新版本 Chrome 浏览器已经不再是 83 版本，所以如果程序不能正常运行请重新下载 [webdriver](http://chromedriver.storage.googleapis.com/index.html) 并自行替换**

### Firefox for Linux 版需要的配置有（注：该版本无法在 Windows 电脑上使用，我使用的Linux发行版为 Debian，不保证其他发行版也适用）：

* 最新版本的 Firefox 浏览器（必须，版本号为 77.0.1）

    * 可以通过 `firefox --version` 查看 Firefox 版本号
    * 如果 Firefox 版本不符，请输入下列命令进行升级
      ```bash
        sudo apt update
        sudo apt upgrade
      ```
    * 如果您的主机上并未安装 Firefox，请输入下列命令进行安装
      ```bash
        sudo apt update
        sudo apt upgrade
        sudo apt install firefox
      ```

* 与最新版 Firefox 浏览器对应的 geckodriver 驱动。如果您遇到了驱动与浏览器版本不符的情况，除了升级浏览器外，还应该升级驱动

    * release 中自带了与上述浏览器版本号对应的驱动（我还是很贴心的）
    * 如果需要升级驱动，请自行下载 [geckodriver](https://github.com/mozilla/geckodriver/releases) 最新版，一般选择 64 位系统的安装包，下载完成后替换掉 release 中自带的 geckodriver 即可

* 上述两点都确定之后，可以使用下列命令运行程序（以 1.1 版本为例）

  ```bash
  tar zxvf login1.1_firefox_for_linux.tar.gz    # 解压压缩文件
  cd login1.1_firefox_for_linux                 # 跳转到目标目录
  ./login1.1_firefox_for_linux                  # 运行程序

  # 如果您是远程ssh到目标 Linux 主机的，建议使用 nohup 挂起，但是第一次运行程序时不可以挂起，因为要输入账号密码
  # nohup ./login1.1_firefox_for_linux &
  ```

### Firefox for Linux(Group Edition)

2020年6月30日晚，东南大学研究生院发布通知说2019级硕士生将于2021年春季才能开学，愤恨之余，想到居然还强制要求每人每天打卡报平安，属实不妥。因而在原有代码基础上增添了团队版本，配合网页端可以帮助大部分人打卡（即一台主机可以同时帮多人打卡）。届时只需要在网页上登录一次，就永远不用担心需要打卡了。

网页端后续如果有时间我会着手来写。

TO DO LIST：

1. 网页端登入（前端代码）
2. 密码检验
3. 邮件提醒
4. 数据库存储

### Edge 版需要的配置有：

* 最新版Chromium内核的64位Edge浏览器（必须，版本号为83.0.478.45）
* 请务必确认Edge浏览器的缩放比例为100%
* Edge浏览器无法后台静默运行，也无法隐藏log，因而为了极致使用体验还是建议使用Chrome

### IE 版需要的配置有（IE同样无法后台静默运行，开发计划无限搁浅）：

* 最新版IE浏览器（必须）
* 请务必保证IE浏览器的缩放比例为100%，工具-缩放请务必选择100%，建议提前打开IE浏览器查看缩放比例
* 请务必关闭IE保护模式，请前往工具-Internet选项-安全，将Internet，本地Internet，受信任的站点，受限制的站点这四个区域的下方方框——启用保护模式（要求重新启动Internet Explorer）前面的勾都去掉，然后点击确认并重启浏览器确认这四个区域的保护模式都已经关闭
* 建议将seu.edu.cn加入到IE的兼容性视图，兼容性视图设置在工具-兼容性视图设置

## Warning

* 升级浏览器后如果程序不能运行，则需要重新下载webdriver并自行替换

    Edge Webdriver 下载地址：https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

    Chrome Webdriver 下载地址：http://chromedriver.storage.googleapis.com/index.html

* 如果第一次您的密码输入错误，请自行寻找loginData.txt（v1.2及以前） or loginData.json（v1.3及以后）文档并修改成正确的账号密码

* 如果您遇到下面提示：`未知错误 Message: unkown error: cannot find Chrome binary`，则表示您的Chrome浏览器未安装或者安装位置并不是系统默认位置：`C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`

    如果是 v1.2 及以前版本，请找到 loginData.txt 文件，并在文件的第三行（前两行分别是您账号和密码）补上您的 Chrome 的安装位置（如果是系统默认位置则不需要添加），格式一般为：`X:\Google\Chrome\Application\chrome.exe`，其中X为盘符
    
    如果是 v1.3 及以后版本，请找到 loginData.json 文件，并在 "loc" 后添加您的 Chrome 的安装位置，此时正确的配置文件格式一般为：{"username": "1111111", "password": "ABABABABABAB", "loc": "X:\Google\Chrome\Application\chrome.exe", "destination": "教务处380"}

