from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By  # 按照什么方式查找，By.ID,By.CSS_SELECTOR
from selenium.webdriver.common.keys import Keys  # 键盘按键操作
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait  # 等待页面加载某些元素
from selenium.webdriver.firefox.options import Options
import time
import random
import json


# 加启动配置 禁用日志log
firefox_opt = Options()
firefox_opt.add_argument('–no-sandbox')  # “–no - sandbox”参数是让root权限下跑
firefox_opt.add_argument('--start-maximized')  # 最大化
firefox_opt.add_argument('--incognito')  # 无痕隐身模式
firefox_opt.add_argument("disable-cache")  # 禁用缓存
firefox_opt.add_argument('log-level=3')
firefox_opt.add_argument('disable-infobars')
firefox_opt.add_argument('--headless')
url = "https://newids.seu.edu.cn/authserver/login?service=http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/*default/index.do"


def writeLog(text):  # 创建打卡记录log文件
    with open('log', 'a') as f:
        s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' ' + text
        print(s)
        f.write(s + '\n')
        f.close()


def getUserData():
    # 读取账号密码文件
    try:
        with open("loginData.json", mode='r', encoding='utf-8') as f:
            # 去掉换行符
            lines = f.readlines()  # 每一行json文件包含一位用户的信息
            f.close()

    # 这里其实是作为测试使用
    except FileNotFoundError:
        print("Welcome to AUTO DO THE F***ING DAILY JOB, copyrights belong to S.H.")
        with open("loginData.json", mode='w', encoding='utf-8') as f:
            user = input('Please Enter Your Username: ')
            pw = input('Then Please Enter Your Password: ')
            email_address = input('Then Please Enter Your Email Address: ')
            loginData = {"username": user, "password": pw,
                         "email_address": email_address}
            loginData = json.dumps(loginData) + '\n'
            lines = [loginData]
            f.write(loginData)
            f.close()

    return lines


def check(text, browser):  # 检查是否无text按钮
    buttons = browser.find_elements_by_tag_name('button')
    for button in buttons:
        if button.get_attribute("textContent").find(text) >= 0:
            return True
    return False


def newTab(browser):
    # browser.get('https://www.baidu.com')
    # 这是只是增加一个无关标签页，使得关闭标签页不退出浏览器
    browser.execute_script("window.open('http://www.baidu.com')")
    windows = browser.current_window_handle  # 定位当前页面句柄
    all_handles = browser.window_handles  # 获取全部页面句柄
    for handle in all_handles:  # 遍历全部页面句柄
        if handle is not windows:  # 判断条件
            browser.switch_to.window(handle)  # 切换到新页面


def login(user, pw, browser, first_handle):  # 打卡主程序
    newTab(browser)
    # browser.delete_all_cookies()
    browser.get(url)
    browser.implicitly_wait(10)

    # 填写用户名密码
    username = browser.find_element_by_id('username')
    password = browser.find_element_by_id('password')
    username.clear()
    password.clear()
    username.send_keys(user)
    password.send_keys(pw)

    # 点击登录
    login_button = browser.find_element_by_class_name('auth_login_btn')
    login_button.submit()

    browser.implicitly_wait(10)
    time.sleep(10)

    # 确认是否打卡成功
    # 的确无新增按钮
    dailyDone = not check("新增", browser)  # 今日是否已经打卡
    if dailyDone is True and check("退出", browser) is True:  # 今日已完成打卡
        writeLog(user + "今日已完成打卡任务")
        browser.close()  # 由于后面的人还需要打卡，因而这里只是关闭标签页
        browser.switch_to.window(first_handle)
        logout(browser)
        print("------------------标签页已关闭----------------------")

    elif dailyDone is False:  # 今日未完成打卡
        # 点击报平安
        buttons = browser.find_elements_by_css_selector('button')
        for button in buttons:
            if button.get_attribute("textContent").find("新增") >= 0:
                button.click()
                browser.implicitly_wait(10)

                # 输入温度再36.5°~37°之间的随机值
                inputfileds = browser.find_elements_by_tag_name(
                    'input')
                for i in inputfileds:
                    if i.get_attribute("placeholder").find("请输入当天晨检体温") >= 0:
                        i.click()
                        i.send_keys(str(random.randint(365, 370)/10.0))

                        # 确认并提交
                        buttons = browser.find_elements_by_tag_name(
                            'button')
                        for button in buttons:
                            if button.get_attribute("textContent").find("确认并提交") >= 0:
                                button.click()
                                buttons = browser.find_elements_by_tag_name(
                                    'button')
                                button = buttons[-1]
                                # 提交
                                if button.get_attribute("textContent").find("确定") >= 0:
                                    button.click()
                                    dailyDone = True  # 标记已完成打卡
                                    writeLog(user + "打卡成功")
                                break
                        break
                break
        browser.close()  # 由于后面的人还需要打卡，因而这里只是关闭标签页
        browser.switch_to.window(first_handle)
        logout(browser)
        print("------------------标签页已关闭----------------------")
        time.sleep(10)  # 昏睡10s
    else:
        browser.close()
        browser.switch_to.window(first_handle)
        logout(browser)
        print("------------------网站出现故障----------------------")
        print("------------------标签页已关闭----------------------")
        time.sleep(300)  # 昏睡5min

    return dailyDone


def logout(browser):  # 坑人的 SEU 会记录登录的ip和浏览器导致即使关闭标签页也无法退出登录，为下一位同学的登录带来问题
    browser.get("https://newids.seu.edu.cn/authserver/index.do")  # 这是登录认证界面
    browser.implicitly_wait(10)
    button = browser.find_element_by_id("logout")
    button.click()


if __name__ == "__main__":
    lines = getUserData()

    localtime = time.localtime(time.time())
    set_minite = localtime.tm_min  # 首次登陆的分钟时刻，代表以后每次在此分钟时刻打卡
    set_hour = localtime.tm_hour  # 首次登陆的时钟时刻，代表以后每次在此时钟时刻打卡

    if set_hour > 9:
        set_hour = 7  # 如果首次登录超过上午10点，则以后默认在7点钟打卡
        first_time = True

    while True:
        try:
            # 登录打卡一次试一试
            browser = webdriver.Firefox(executable_path='./geckodriver', options=firefox_opt)
            browser.get('https://www.baidu.com')
            first_handle = browser.current_window_handle  # 第一个窗口
            print("------------------浏览器已启动----------------------")

            for l in lines:  # 帮每一个成员打卡
                loginData = json.loads(str(l).strip())
                user = loginData['username']
                pw = loginData['password']
                email = loginData['email_address']

                while True:
                    try:
                        dailyDone = login(user, pw, browser, first_handle)
                        if dailyDone is False:
                            time.sleep(10)  # 昏睡10s
                            continue  # 当由于某些原因该成员无法成功打卡，则重新打卡

                    except Exception as r:  # 当打卡出现未知错误时对该成员重新打卡
                        print("未知错误 %s" % (r))
                        time.sleep(10)  # 昏睡10s
                        continue

                    break

            # 当所有成员当天均成功打卡，则关闭浏览器并昏睡到明天
            sleep_time = (set_hour+24-time.localtime(time.time()).tm_hour) * \
                3600 + (set_minite-time.localtime(time.time()).tm_min)*60
            writeLog("下次打卡开始时间：明天" + str(set_hour) + ':' +
                     str(set_minite) + "，" + "即" + str(sleep_time) + 's后')
            browser.quit()
            print("------------------浏览器已关闭----------------------")
            time.sleep(sleep_time)

        except Exception as r:
            print("未知错误 %s" % (r))
            time.sleep(10)  # 昏睡10s
