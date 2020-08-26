from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By  # 按照什么方式查找，By.ID,By.CSS_SELECTOR
from selenium.webdriver.common.keys import Keys  # 键盘按键操作
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait  # 等待页面加载某些元素
from selenium.webdriver.chrome.options import Options
from datetime import date, timedelta
import time
import random
import json
import re


# 加启动配置 禁用日志log
chrome_options = Options()
# “–no - sandbox”参数是让Chrome在root权限下跑
chrome_options.add_argument('–no-sandbox')
chrome_options.add_argument('–disable-dev-shm-usage')
chrome_options.add_experimental_option(
    'excludeSwitches', ['enable-automation'])
chrome_options.add_argument('--start-maximized')  # 最大化
chrome_options.add_argument('--incognito')  # 无痕隐身模式
chrome_options.add_argument("disable-cache")  # 禁用缓存
chrome_options.add_argument('log-level=3')
chrome_options.add_argument('disable-infobars')
chrome_options.add_argument('--headless')

url = "https://newids.seu.edu.cn/authserver/login?service=http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/*default/index.do"
enter_campus_url = "http://ehall.seu.edu.cn/qljfwapp3/sys/lwWiseduElectronicPass/*default/index.do#/"  # 申请入校网址
dailyDone = False  # 今日是否已经打卡

# 创建打卡记录log文件


def writeLog(text):
    with open('log.txt', 'a') as f:
        s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' ' + text
        print(s)
        f.write(s + '\n')
        f.close()


# 创建账号密码文件，以后都不用重复输入
# 1.1版本之后更新可以读取 chrome.exe 的位置，防止用户Chrome浏览器未安装到默认位置导致的程序无法执行
# 1.3版本之后重大更新，改用json文件格式存储信息，同时可以读取“所到楼宇”等信息，用于第二日进校申请
def getUserData():
    # 读取账号密码文件
    try:
        with open("loginData.json", mode='r', encoding='utf-8') as f:
            # 去掉换行符
            loginData = f.readline()
            f.close()

    # 写入账号密码文件
    except FileNotFoundError:
        print("Welcome to AUTO DO THE F***ING DAILY JOB, copyrights belong to S.H.")
        with open("loginData.json", mode='w', encoding='utf-8') as f:
            user = input('Please Enter Your Username: ')
            pw = input('Then Please Enter Your Password: ')
            loginData = {"username": user, "password": pw,
                         "loc": "", "destination": ""}
            loginData = json.dumps(loginData) + '\n'
            f.write(loginData)
            f.close()

    return loginData

def login(user, pw, browser):
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

# 检查是否无text按钮
def check(text, browser):
    buttons = browser.find_elements_by_tag_name('button')
    for button in buttons:
        if button.get_attribute("textContent").find(text) >= 0:
            return True
    return False

# 检查第二日入校是否已申请
def checkEnterCampus(browser):
    browser.get(enter_campus_url)
    browser.implicitly_wait(10)
    time.sleep(10)

    date_info_raw = browser.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div/div[2]/span[2]")
    date_info = re.findall(r"\d+\.?\d*",date_info_raw.text)
    year_info = date_info[0]
    month_info = date_info[1]
    day_info = date_info[2]

    today_year = date.today().strftime("%Y")
    today_month = date.today().strftime("%m")
    today_day = date.today().strftime("%d")

    if year_info == today_year and month_info == today_month and day_info == today_day:
        return True
    else:
        return False

# 检查是否已经超过入校申请时间
def checkEnterCampusTime():
    localtime = time.localtime(time.time())
    hour = localtime.tm_hour  
    minite = localtime.tm_min

    if hour >= 12 or (hour == 11 and minite > 45):   # 超过11:45则无法打卡（打卡程序运行也需要一点时间
        return True
    else:
        return False

# 开始申请第二日入校
def enterCampus(browser, destination):
    # 获取当下时间信息
    tomorrow_year = (date.today() + timedelta(days=1)).strftime("%Y")
    tomorrow_month = (date.today() + timedelta(days=1)).strftime("%m")
    tomorrow_day = (date.today() + timedelta(days=1)).strftime("%d")

    # 检查今天是否已申请
    if checkEnterCampus(browser) == True:
        s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' ' + "今日已申请第二日入校"
        print(s)

    # 检查是否超过打卡时间
    elif checkEnterCampusTime() == True:
        s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' ' + "已超过入校申请时间"
        print(s)

    else:
        s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' ' + "正在申请第二日入校"
        print(s)

        browser.get(enter_campus_url)
        browser.implicitly_wait(10)
        time.sleep(10)

        # 点击加号
        js = "document.querySelector(\"#app > div > div.mint-fixed-button.mt-color-white.turn-add-but.mint-fixed-button--bottom-right.mint-fixed-button--primary.mt-bg-primary\").click();"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 1.工作场所是否符合防护要求
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(19) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 1.先点否
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(19) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li.mt-picker-column-item.mt-color-grey\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 1.再点是
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(19) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li.mt-picker-column-item.mt-color-grey\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 1.最后点确认
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(19) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 2.工作人员能否做好个人防护
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(20) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 2.先点否
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(20) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li.mt-picker-column-item.mt-color-grey\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 2.再点是
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(20) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li.mt-picker-column-item.mt-color-grey\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 2.最后点确认
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(20) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 3.是否已在南京居家隔离满14天
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(5) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 3.先点否
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(5) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li.mt-picker-column-item.mt-color-grey\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 3.再点是
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(5) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li.mt-picker-column-item.mt-color-grey\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 3.最后点确认
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(5) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 4.目前身体是否健康
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 4.先点否
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li.mt-picker-column-item.mt-color-grey\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 4.再点是
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li.mt-picker-column-item.mt-color-grey\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 4.最后点确认
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 5.通行区域
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(1) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 5.点击校区
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(1) > div > div > div.mint-box-group > div > div > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > div.mint-cell-title > div > label > span.mint-checkbox-new > span\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 5.最后点确认
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(1) > div > div > div.mint-selected-footer.__emapm > div.mint-selected-footer-bar > button.mint-button.mint-selected-footer-confirm.mt-btn-primary.mint-button--large\").click();"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 6. 通行开始时间
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定年份
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(1) > ul > li:nth-child(" + str(int(tomorrow_year)-1919) + ")\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定月份
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(2) > ul > li:nth-child(" + tomorrow_month + ")\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定日期
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(3) > ul > li:nth-child(" + tomorrow_day + ")\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定小时 8
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(4) > ul > li:nth-child(9)\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定分钟 31
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(5) > ul > li:nth-child(32)\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6.最后点确认
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 6. 通行结束时间
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定年份
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(1) > ul > li:nth-child(" + str(int(tomorrow_year)-1919) + ")\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定月份
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(2) > ul > li:nth-child(" + tomorrow_month + ")\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定日期
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(3) > ul > li:nth-child(" + tomorrow_day + ")\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定小时 20
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(4) > ul > li:nth-child(21)\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 确定分钟 31
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(5) > ul > li:nth-child(32)\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 6. 最后点确认
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 7. 所到楼宇
        js = "window.inputValue = function (dom, st) {\
                var evt = new InputEvent('input', {\
                inputType: 'insertText',\
                data: st,\
                dataTransfer: null,\
                isComposing: false\
                });\
                dom.value = st;\
                dom.dispatchEvent(evt);\
            }"
        browser.execute_script(js)
        time.sleep(1)

        # 7. 输入值
        js = "window.inputValue(document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(4) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > div.mint-cell-value.mt-color-grey > input\"),\"" + destination + "\")"
        browser.execute_script(js)
        time.sleep(1)

        #####################################################################################
        # 8. 申请理由
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 8. 到办公室科研
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li:nth-child(3)\").click();"
        browser.execute_script(js)
        time.sleep(1)

        # 8. 最后点确认
        js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
        browser.execute_script(js)
        time.sleep(1)


        #####################################################################################
        # 9. 提交
        js = "document.querySelector(\"#app > div > div.mint-fixed-container.mint-fixed-container--bottom > div > div.emap-flow-buttons > button\").click();"
        browser.execute_script(js)
        time.sleep(5)

        # 9. 确认
        js = "document.querySelector(\"body > div.mint-msgbox-wrapper > div > div.mint-msgbox-btns > button.mint-msgbox-btn.mint-msgbox-confirm.mt-btn-primary\").click();"
        browser.execute_script(js)
        time.sleep(5)
        
        #####################################################################################
        # 10. log
        writeLog("已完成第二日入校申请")


if __name__ == "__main__":
    # user, pw, browser_loc = enterUserPW()
    userData = getUserData()
    loginData = json.loads(str(userData).strip())
    user = loginData['username']
    pw = loginData['password']
    browser_loc = loginData['loc']
    destination = loginData['destination']

    # 判断是否写入非默认安装位置的 Chrome 位置
    if len(browser_loc) > 10:
        chrome_options.binary_location = browser_loc
    
    # 判断是否写入“所到楼宇”，如果写入，则会进行第二日入校申请；否则，不进行第二日入校申请，仅单纯打卡报平安
    # 默认情况下是不进行申请的
    if len(destination) > 1:
        enterCampusRequist = True
    else:
        enterCampusRequist = False

    localtime = time.localtime(time.time())
    set_minite = localtime.tm_min  # 首次登陆的分钟时刻，代表以后每次在此分钟时刻打卡
    set_hour = localtime.tm_hour  # 首次登陆的时钟时刻，代表以后每次在此时钟时刻打卡

    if set_hour > 9:
        set_hour = 7  # 如果首次登录超过上午10点，则以后默认在7点钟打卡
        first_time = True

    while True:
        try:
            # 登录打卡一次试一试
            browser = webdriver.Chrome(
                './chromedriver', options=chrome_options)
            print("------------------浏览器已启动----------------------")
            login(user, pw, browser)
            browser.implicitly_wait(10)
            time.sleep(10)

            # 确认是否打卡成功
            # 的确无新增按钮
            dailyDone = not check("新增", browser)
            if dailyDone is True and check("退出", browser) is True:  # 今日已完成打卡
                sleep_time = (set_hour+24-time.localtime(time.time()).tm_hour) * \
                    3600 + (set_minite-time.localtime(time.time()).tm_min)*60
                writeLog("下次打卡时间：明天" + str(set_hour) + ':' +
                         str(set_minite) + "，" + "即" + str(sleep_time) + 's后')

                # 1.3 版本更新每日入校申请，自动申请第二日入校
                if enterCampusRequist is True:
                    enterCampus(browser, destination)
                    if checkEnterCampus(browser) is True: # 再确认一次，以免学校改版导致程序出错
                        writeLog("再次确认：本次未成功申请第二日入校")

                browser.quit()
                print("------------------浏览器已关闭----------------------")
                time.sleep(sleep_time)
            elif dailyDone is False:  # 今日未完成打卡
                # 点击报平安
                buttons = browser.find_elements_by_css_selector('button')
                for button in buttons:
                    if button.get_attribute("textContent").find("新增") >= 0:
                        button.click()
                        browser.implicitly_wait(10)

                        # 输入温度36.5-37°之间随机值
                        inputfileds = browser.find_elements_by_tag_name(
                            'input')
                        for i in inputfileds:
                            if i.get_attribute("placeholder").find("请输入当天晨检体温") >= 0:
                                i.click()
                                i.send_keys(str(random.randint(365, 370)/10.0))

                                # 1.2版本新增，“24h内，密切接触人员有无发热或呼吸道症状”选项填写
                                # 选择该选项框
                                js = "document.querySelector(\"#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(51) > div > a\").click();"
                                browser.execute_script(js)
                                time.sleep(1)
                                # 反复横跳，先选择其他按钮
                                js = "document.querySelector(\"#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(51) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li:nth-child(2)\").click()"
                                browser.execute_script(js)
                                time.sleep(1)
                                # 选择“无”
                                js = "document.querySelector(\"#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(51) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li:nth-child(1)\").click();"
                                browser.execute_script(js)
                                time.sleep(1)
                                # 点击“确定”
                                js = "document.querySelector(\"#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(51) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click()"
                                browser.execute_script(js)

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
                                            writeLog("打卡成功")
                                        else:
                                            print("WARNING: 学校可能改版，请及时更新脚本")
                                        break
                                break
                        break
                browser.quit()
                print("------------------浏览器已关闭----------------------")
                time.sleep(10)  # 昏睡10s 为了防止网络故障未打上卡
            else:
                browser.close()
                print("------------------网站出现故障----------------------")
                print("------------------浏览器已关闭----------------------")
                time.sleep(300)  # 昏睡5min 为了防止网络故障未打上卡
        except Exception as r:
            print("未知错误 %s" % (r))
