from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# 等待页面加载完成，找到某个条件发生后再继续执行后续代码，如果超过设置时间检测不到则抛出异常
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By                         # 支持的定位器分类
from selenium.webdriver.support import expected_conditions as EC    # 判断元素是否加载
from datetime import date, timedelta
import json
import smtplib
from email.mime.text import MIMEText                # 用于构建邮件内容
from email.header import Header                     # 用于构建邮件头
import time, random, re, requests, winreg, zipfile

# 加启动配置 禁用日志log
chrome_opt = Options()
# –no - sandbox 参数是让root权限下跑
chrome_opt.add_argument('–no-sandbox')
chrome_opt.add_argument('--start-maximized')       # 最大化
chrome_opt.add_argument('--incognito')             # 无痕隐身模式
chrome_opt.add_argument("disable-cache")           # 禁用缓存
chrome_opt.add_argument('log-level=3')
chrome_opt.add_argument('disable-infobars')
chrome_opt.add_argument('--headless')

# 可执行文件地址
file_executable_path = './chromedriver.exe'  # for Chrome
# file_executable_path = './geckodriver'      # for Firefox

# 打卡网址
login_url = "https://newids.seu.edu.cn/authserver/login?service=http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/*default/index.do"
# 申请入校网址
enter_campus_url = "http://ehall.seu.edu.cn/qljfwapp3/sys/lwWiseduElectronicPass/*default/index.do#/"
# 登出网址
logout_url = "https://newids.seu.edu.cn/authserver/index.do"


def writeLog(text):  # 创建打卡记录log文件
    with open('log', 'a') as f:
        s = '[' + time.strftime("%Y-%m-%d %H:%M:%S",
                                time.localtime()) + '] ' + text
        print(s)
        f.write(s + '\n')
        f.close()
        return s


def mailMsg(user, text):
    mail_msg = '[' + time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()) + '] [' + user + ']：<font color="blue">' + text + "</font>"
    mail_msg = "<p>" + mail_msg + "</p>"
    return mail_msg


def waitByXPath(browser, loc, timeout=15):
    return WebDriverWait(browser, timeout, 0.5).until(EC.presence_of_element_located((By.XPATH, loc)))


def getUserData():
    # 创建账号密码文件，以后都不用重复输入
    # 1.3版本之后可以读取“所到楼宇”等信息，用于第二日进校申请
    try:
        with open("loginData.json", mode='r', encoding='utf-8') as f:   # 读取账号密码文件
            # 去掉换行符
            # 每一行json文件包含一位用户的信息
            lines = f.readlines()
            f.close()

    # 这里其实是作为测试使用
    except FileNotFoundError:
        print("Welcome to AUTO DO THE F***ING DAILY JOB, copyrights belong to S.H.")
        with open("loginData.json", mode='w', encoding='utf-8') as f:
            user = input('Please Enter Your Username: ')
            pw = input('Then Please Enter Your Password: ')
            email_address = input('Then Please Enter Your Email Address: ')
            loginData = {"username": user, "password": pw,
                         "email_address": email_address, "destination": "", "name": "Li Lei", "phone": "123456789", "hold_on": "False"}
            loginData = json.dumps(loginData, ensure_ascii=False) + '\n'
            lines = [loginData]
            f.write(loginData)
            f.close()

    return lines


def login(user, pw, url, browser):   # 登录打卡界面/申请第二日入校界面
    if url is login_url:
        browser.get(url)

        # 等待用户名和密码框加载完成
        username_field = WebDriverWait(browser, 15, 0.5).until(
            EC.presence_of_element_located((By.ID, 'username')))
        password_field = WebDriverWait(browser, 15, 0.5).until(
            EC.presence_of_element_located((By.ID, 'password')))
        if username_field and password_field:
            username_field.clear()
            password_field.clear()

            username_field.send_keys(user)
            password_field.send_keys(pw)

            login_button = browser.find_element_by_class_name('auth_login_btn')
            login_button.submit()

        else:
            writeLog("------------------网站出现故障----------------------")
            return False

        # 等待打卡页面加载完成（这里是看"基本信息上报"是否加载完成）
        try:
            waitByXPath(browser, '//*[@id="app"]/div/div[1]/button')
            return True
        except:
            writeLog("------------------等待打卡页面出现故障----------------------")
            return False

    elif url is enter_campus_url:
        browser.get(enter_campus_url)

        if waitByXPath(browser, '/html/body/div[1]/div/div[2]/div/div/div[2]/div/div[2]/span[2]'):
            return True
        else:
            writeLog("------------------网站出现故障----------------------")
            return False

    else:
        writeLog("-------------------URL 错误------------------------")
        return False


def checkEnterCampus(browser):
    # 检查第二日入校是否已申请
    try:
        date_info_raw = browser.find_element_by_xpath(
            "/html/body/div[1]/div/div[2]/div/div/div[2]/div/div[2]/span[2]")
        date_info = re.findall(r"\d+\.?\d*", date_info_raw.text)
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

    except:
        return False


def checkEnterCampusTime():
    # 检查是否已经超过入校申请时间
    localtime = time.localtime(time.time())
    hour = localtime.tm_hour
    minite = localtime.tm_min

    if hour >= 15 or (hour == 14 and minite > 45):   # 超过14:45则无法打卡（打卡程序运行也需要一点时间）
        return True
    else:
        return False


def execute_js_script(browser, js, num):
    try:
        browser.execute_script(js)
    except:
        writeLog(num + " WARNING: 学校可能改版，请及时更新脚本")


def enterCampus(user, pw, name, destination, phone, browser):
    # 开始申请第二日入校
    # 获取当下时间信息
    tomorrow_year = (date.today() + timedelta(days=1)).strftime("%Y")
    tomorrow_month = (date.today() + timedelta(days=1)).strftime("%m")
    tomorrow_day = (date.today() + timedelta(days=1)).strftime("%d")

    if login(user, pw, enter_campus_url, browser) is False:
        writeLog("检查第二日入校是否已申请出现问题")
        return False

    # 检查今天是否已申请
    if checkEnterCampus(browser) == True:
        writeLog(user + name + "：今日已申请第二日入校")

    # 检查是否超过打卡时间
    elif checkEnterCampusTime() == True:
        writeLog(user + name + "：已超过入校申请时间")
        return False

    # 申请第二日入校
    else:
        writeLog(user + name + "：正在申请第二日入校")

        # 点击加号
        js = "document.querySelector(\"#app > div > div.mint-fixed-button.mt-color-white.turn-add-but.mint-fixed-button--bottom-right.mint-fixed-button--primary.mt-bg-primary\").click();"
        execute_js_script(browser, js, '点击加号')

        try:
            submit_button = waitByXPath(
                browser, '//*[@id="app"]/div/div[2]/div/div[1]/button')

            #####################################################################################
            # 1.工作场所是否符合防护要求
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(19) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
            execute_js_script(browser, js, '工作场所是否符合防护要求')

            # 1.确定按钮
            waitByXPath(
                browser, '//*[@id="app"]/div/div[1]/div[2]/div/div[2]/div[19]/div/div[1]/div/div[1]/div[2]')
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(19) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
            execute_js_script(browser, js, '工作场所是否符合防护要求（确定按钮）')

            # 2.工作人员能否做好个人防护
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(20) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
            execute_js_script(browser, js, '工作人员能否做好个人防护')

            # 2.最后点确认
            waitByXPath(
                browser, '//*[@id="app"]/div/div[1]/div[2]/div/div[2]/div[20]/div/div[1]/div/div[1]/div[2]')
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(20) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
            execute_js_script(browser, js, '工作人员能否做好个人防护（确定按钮）')

            #####################################################################################
            # 3.是否已在南京居家隔离满14天
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(5) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
            execute_js_script(browser, js, '是否已在南京居家隔离满14天')

            # 3.最后点确认
            waitByXPath(
                browser, '//*[@id="app"]/div/div[1]/div[3]/div/div[2]/div[5]/div/div[1]/div/div[1]/div[2]')
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(5) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
            execute_js_script(browser, js, '是否已在南京居家隔离满14天（确定按钮）')

            #####################################################################################
            # 4.目前身体是否健康
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
            execute_js_script(browser, js, '目前身体是否健康')

            # 4.最后点确认
            waitByXPath(
                browser, '//*[@id="app"]/div/div[1]/div[3]/div/div[2]/div[6]/div/div[1]/div/div[1]/div[2]')
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(3) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
            execute_js_script(browser, js, '目前身体是否健康（确定按钮）')

            #####################################################################################
            # 5.通行区域
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(1) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
            execute_js_script(browser, js, '通行区域')

            # 5.点击校区
            waitByXPath(
                browser, '//*[@id="app"]/div/div[1]/div[4]/div/div[2]/div[1]/div/div/div[2]/div[1]/button[2]')
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(1) > div > div > div.mint-box-group > div > div > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > div.mint-cell-title > div > label > span.mint-checkbox-new > span\").click();"
            execute_js_script(browser, js, '点击校区')

            # 5.最后点确认
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(1) > div > div > div.mint-selected-footer.__emapm > div.mint-selected-footer-bar > button.mint-button.mint-selected-footer-confirm.mt-btn-primary.mint-button--large\").click();"
            execute_js_script(browser, js, '最后点确认')
            waitByXPath(browser, '//*[@id="app"]/div/div[2]/div/div[1]/button')

            #####################################################################################
            # 6. 通行开始时间
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
            execute_js_script(browser, js, '通行开始时间')
            waitByXPath(
                browser, '//*[@id="app"]/div/div[1]/div[4]/div/div[2]/div[2]/div/div[1]/div/div[1]/div[2]')

            # 6. 确定年份
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(1) > ul > li:nth-child(" + str(int(tomorrow_year)-1919) + ")\").click();"
            execute_js_script(browser, js, '通行开始时间（确定年份）')

            # 6. 确定月份
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(2) > ul > li:nth-child(" + tomorrow_month + ")\").click();"
            execute_js_script(browser, js, '通行开始时间（确定月份）')

            # 6. 确定日期
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(3) > ul > li:nth-child(" + tomorrow_day + ")\").click();"
            execute_js_script(browser, js, '通行开始时间（确定日期）')

            # 6. 确定小时 8
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(4) > ul > li:nth-child(9)\").click();"
            execute_js_script(browser, js, '通行开始时间（确定小时）')

            # 6. 确定分钟 31
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(5) > ul > li:nth-child(32)\").click();"
            execute_js_script(browser, js, '通行开始时间（确定分钟）')

            # 6.最后点确认
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(2) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
            execute_js_script(browser, js, '通行开始时间（最后点确认）')

            #####################################################################################
            # 7. 通行结束时间
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
            execute_js_script(browser, js, '通行结束时间')
            waitByXPath(
                browser, '//*[@id="app"]/div/div[1]/div[4]/div/div[2]/div[3]/div/div[1]/div/div[1]/div[2]')

            # 7. 确定年份
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(1) > ul > li:nth-child(" + str(int(tomorrow_year)-1919) + ")\").click();"
            execute_js_script(browser, js, '通行结束时间（确定年份）')

            # 7. 确定月份
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(2) > ul > li:nth-child(" + tomorrow_month + ")\").click();"
            execute_js_script(browser, js, '通行结束时间（确定月份）')

            # 7. 确定日期
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(3) > ul > li:nth-child(" + tomorrow_day + ")\").click();"
            execute_js_script(browser, js, '通行结束时间（确定日期）')

            # 7. 确定小时 21
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(4) > ul > li:nth-child(22)\").click();"
            execute_js_script(browser, js, '通行结束时间（确定小时）')

            # 7. 确定分钟 59
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__columns > div:nth-child(5) > ul > li:nth-child(60)\").click();"
            execute_js_script(browser, js, '通行结束时间（确定分钟）')

            # 7. 最后点确认
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(3) > div > div.mint-popup.mt-bg-white.mint-datetime.emapm-date-picker.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
            execute_js_script(browser, js, '通行结束时间（最后点确认）')

            #####################################################################################
            # 8. 所到楼宇
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
            execute_js_script(browser, js, '所到楼宇')

            # 8. 输入值
            js = "window.inputValue(document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(4) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > div.mint-cell-value.mt-color-grey > input\"),\"" + destination + "\")"
            execute_js_script(browser, js, '所到楼宇（输入值）')

            #####################################################################################
            # 9. 申请理由
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
            execute_js_script(browser, js, '申请理由')
            waitByXPath(
                browser, '//*[@id="app"]/div/div[1]/div[4]/div/div[2]/div[6]/div/div[1]/div/div[1]/div[2]')

            # 9. 到办公室科研
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li:nth-child(3)\").click();"
            execute_js_script(browser, js, '到办公室科研')

            # 9. 最后点确认
            js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(6) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click();"
            execute_js_script(browser, js, '最后点确认')

            #####################################################################################
            # 10. 提交
            submit_button.click()
            try:
                confirm_button = waitByXPath(
                    browser, '/html/body/div[3]/div/div[3]/button[2]', 2)
                confirm_button.click()
                writeLog("已完成第二日入校申请")

            except:
                # 可能是因为未选择身份证件（by 徐）
                print("WARNING: 可能是因为未选择身份证件")

                #####################################################################################
                # 10.1 选择身份证件
                js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(9) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i\").click();"
                execute_js_script(browser, js, '选择身份证件')
                waitByXPath(
                    browser, '//*[@id="app"]/div/div[1]/div[2]/div/div[2]/div[9]/div/div[1]/div/div[1]/div[2]')

                # 10.1 点击确定
                js = "document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(9) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme\").click()"
                execute_js_script(browser, js, '选择身份证件（点击确定）')

                # 10.1 提交
                submit_button.click()

                try:
                    confirm_button = waitByXPath(
                        browser, '/html/body/div[3]/div/div[3]/button[2]', 2)
                    confirm_button.click()
                    writeLog("已完成第二日入校申请")

                except:
                    # 可能是因为未填写联系方式（by 丘）
                    print("WARNING: 可能是因为未填写联系方式")

                    #####################################################################################
                    # 10.2 填写联系方式
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
                    execute_js_script(browser, js, '填写联系方式')

                    # 10.2 输入值
                    js = "window.inputValue(document.querySelector(\"#app > div > div.emapm-form > div:nth-child(2) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(5) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > div.mint-cell-value.mt-color-grey > input\"),\"" + phone + "\")"
                    execute_js_script(browser, js, '填写联系方式（输入值）')

                    # 10.2 提交
                    submit_button.click()

                    # 10.2 确认
                    try:
                        confirm_button = waitByXPath(
                            browser, '/html/body/div[3]/div/div[3]/button[2]', 2)
                        confirm_button.click()
                        writeLog("已完成第二日入校申请")

                    except:
                        writeLog("未完成第二日入校申请")
                        return False

        except:
            writeLog("未完成第二日入校申请")
            return False

    # 等待回到原界面
    if waitByXPath(browser, '/html/body/div[1]/div/div[2]/div/div/div[2]/div/div[2]/span[2]'):
        browser.refresh()
        waitByXPath(
            browser, '/html/body/div[1]/div/div[2]/div/div/div[2]/div/div[2]/span[2]')
        return True
    else:
        writeLog("------------------网站出现故障----------------------")
        return False


def checkIn(user, name, browser):
    # 检查是否存在新增按钮
    time.sleep(1)
    buttons = browser.find_elements_by_tag_name('button')
    daily_done = True
    for button in buttons:
        if button.get_attribute("textContent").find("新增") >= 0:
            new_button = button
            daily_done = False
            break

    # 检查是否存在退出按钮
    exit_button = browser.find_element_by_xpath(
        '//*[@id="app"]/div/div[1]/button')

    if daily_done is True and exit_button:        # 今日已完成打卡
        writeLog(user + name + "：今日已完成打卡任务")

    elif daily_done is False and exit_button:     # 今日未完成打卡
        # 点击报平安
        new_button.click()

        time.sleep(2)

        # 输入当天晨检体温, 36.5-37之间的随机值
        input_filed = waitByXPath(
            browser, '//*[@id="app"]/div/div/div[2]/div/div[4]/div/div[2]/div[1]/div/a/div[2]/div[2]/input')
        if input_filed:
            input_filed.click()
            input_filed.send_keys(str(random.randint(365, 370)/10.0))

        else:
            writeLog("------------------网站出现故障----------------------")
            return False

        # 1.5版本更新，确定目前所在位置
        #####################################################################################
        # 获取目前所在位置
        loc = browser.find_element_by_xpath(
            '//*[@id="app"]/div/div/div[2]/div/div[4]/div/div[2]/div[4]/div/a/div[2]/div[2]/div').get_attribute("innerHTML")
        writeLog(user + name + "：" + loc)

        if not (loc == "在校内" or loc == "在校外(在南京)"):
            # time.sleep(1000)
            # 目前所在位置统一为[在校内]
            js = 'document.querySelector("#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(4) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i").click();'
            execute_js_script(browser, js, '目前所在位置')

            # 选择[在校内]
            waitByXPath(
                browser, '//*[@id="app"]/div/div/div[2]/div/div[4]/div/div[2]/div[4]/div/div[1]/div/div[1]')
            js = 'document.querySelector("#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(4) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__columns > div > ul > li:nth-child(2)").click();'
            execute_js_script(browser, js, '目前所在位置（在校内）')

            # 点击确定
            js = 'document.querySelector("#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(4) > div > div.mint-popup.mt-bg-white.mint-popup-bottom > div > div.mint-picker__toolbar.mt-bColor-grey-lv6 > div.mint-picker__confirm.mt-color-theme").click();'
            execute_js_script(browser, js, '目前所在位置（确定按钮）')

            # 目前所在校区统一为[在四牌楼校区]
            js = 'document.querySelector("#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(8) > div > a > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > i").click();'
            execute_js_script(browser, js, '目前所在校区')

            # 选择[四牌楼校区]
            waitByXPath(
                browser, '//*[@id="app"]/div/div/div[2]/div/div[4]/div/div[2]/div[8]/div/div/div[2]/button')
            js = 'document.querySelector("#app > div > div > div:nth-child(2) > div > div:nth-child(4) > div > div.mint-cell-group-content.mint-hairline--top-bottom.mt-bg-white.mt-bColor-after-grey-lv5 > div:nth-child(8) > div > div > div.mint-box-group > div > div > div > a:nth-child(2) > div.mint-cell-wrapper.mt-bColor-grey-lv5.mint-cell-no-bottom-line > div.mint-cell-title > label > span.mint-radiobox").click();'
            execute_js_script(browser, js, '目前所在校区（四牌楼校区）')
            time.sleep(3)
            # waitByXPath(
            # browser, '//*[@id="app"]/div/div/div[3]/button')

        # time.sleep(1000)
        # 确认并提交
        submit_button = browser.find_element_by_xpath(
            '//*[@id="app"]/div/div/div[3]/button')
        submit_button.click()

        time.sleep(1)

        # 提交
        confirm_buttons = (browser.find_elements_by_tag_name('button'))[-1]
        if confirm_buttons.get_attribute("textContent").find("确定") >= 0:
            confirm_buttons.click()

            # 确认"基本信息上报"加载完成
            if waitByXPath(browser, '//*[@id="app"]/div/div[2]/a[2]/div[2]'):
                daily_done = True     # 标记已完成打卡
                writeLog(user + name + "：打卡成功")

            else:
                writeLog("------------------网站出现故障----------------------")

        else:
            writeLog(user + name + "：本次打卡失败")
            return "无法点击提交按钮"

    else:
        writeLog("------------------网站出现奇奇怪怪的故障----------------------")
        time.sleep(300)  # 昏睡5min
        return False

    return daily_done


def logout(browser):
    # 坑人的 SEU 会记录登录的ip和浏览器导致即使关闭标签页也无法退出登录，为下一位同学的登录带来问题
    browser.get(logout_url)  # 这是登录认证界面

    logout_button = WebDriverWait(browser, 15, 0.5).until(
        EC.presence_of_element_located((By.ID, 'logout')))

    if logout_button:
        logout_button.click()

        successfully_logout_banner = waitByXPath(
            browser, '/html/body/div[2]/div[1]/div/div/div/h2')

    if logout is False or successfully_logout_banner is False:
        writeLog("------------------网站出现故障----------------------")
        browser.quit()
        time.sleep(2)  # 昏睡2s
        browser = webdriver.Chrome(
            executable_path=file_executable_path, options=chrome_opt)

    return browser


def sendMail(mail_msg, to_addr):
    # 发送邮件提醒自己
    # 发信方的信息：发信邮箱，QQ 邮箱授权码
    # 此处是我私人的信息，注意不要泄露
    from_addr = 'example@example.com'
    cc_mail = from_addr
    password = 'password'

    # mail_msg 添加签名
    mail_msg += """
    <br /><br />
    <hr />
    <p>Welcome to use <a href="https://www.typex.ltd">AutoLogin</a>,
    you can also visit our <a href="https://github.com/StephenHoo/AutoLogin">Github Repository</a> to get more information.</p>
    <p>This is an automated email, <b>reply this email</b> to <b>unsubscribe</b> from these notifications. </p><br />

    Sincerely, <br />
    The TYPEX team <br />
    """

    # 发信服务器
    smtp_server = 'smtp.qq.com'
    # smtp_server = 'smtp.163.com'

    # 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
    msg = MIMEText(mail_msg, 'html', 'utf-8')

    # 邮件头信息
    msg['From'] = Header(from_addr)
    msg['To'] = Header(to_addr)
    msg['Cc'] = Header(cc_mail)
    msg['Subject'] = Header('AutoLogin Information')

    # 开启发信服务，这里使用的是加密传输
    try:
        server = smtplib.SMTP_SSL(smtp_server)
        server.connect(smtp_server, 465)
        # 登录发信邮箱
        server.login(from_addr, password)
        # 发送邮件
        server.sendmail(from_addr, to_addr, msg.as_string())
        # 关闭服务器
        server.quit()

        writeLog("已成功发送邮件")
    except Exception as r:  # 当出现错误的时候就不发送邮件了
        writeLog("邮件发送出现未知错误 %s" % (r))

def unzip_single(src_file, dest_dir):
    zf = zipfile.ZipFile(src_file)
    zf.extractall(path=dest_dir)
    zf.close()

def update_drv_version():
    url = 'http://npm.taobao.org/mirrors/chromedriver/'
    rep = requests.get(url).text
    real_driver_version = {}
    result = re.compile(r'\d.*?/</a>.*?Z').findall(rep)

    for i in result:
        version = re.compile(r'.*?/').findall(i)[0]
        print(version.split('.')[0])
        real_driver_version[version.split('.')[0]] = version

    ChromeBroserVersion = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,'SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome'),'DisplayVersion')[0]
    ChromeVersion = ChromeBroserVersion.split('.')[0]

    if int(ChromeVersion) < 70:
        print("really old chrome browser, please update your browser to 70 or later!")
    print("downloading new chromedriver...\n")
    download_url = url + real_driver_version[ChromeVersion] + 'chromedriver_win32.zip'
    file = requests.get(download_url)
    with open("chromedriver_win32.zip", 'wb') as zip_file:
        zip_file.write(file.content)
    unzip_single('chromedriver_win32.zip','')

if __name__ == "__main__":
    set_hour = 2        # 默认2：2开始打卡
    set_minite = 2

    while True:
        # sleep_time = (set_hour+24-time.localtime(time.time()).tm_hour) * \
        #     3600 + (set_minite-time.localtime(time.time()).tm_min)*60
        # writeLog("下次打卡开始时间：明天" + str(set_hour) + ':' +
        #          str(set_minite) + "，" + "即" + str(sleep_time) + 's后')
        # writeLog("###################################################")
        # time.sleep(sleep_time)

        try:
            user_data_lines = getUserData()     # 获取用户信息
            error_user_data_lines = []          # 未成功打卡的用户信息
            user_num = len(user_data_lines)     # 总的用户人数
            hold_on_user_num = 0                # 挂起的用户人数
            complete_user_num = 0               # 已完成的打卡人数
            enter_campus_num = 0                # 申请入校的总人数
            complete_enter_campus_num = 0       # 已完成申请第二日入校的总人数

            try:
                browser = webdriver.Chrome(executable_path=file_executable_path,options=chrome_opt)
            except:
                print("Old chromedriver detected, updating...\n")
                update_drv_version()
                browser = webdriver.Chrome('./chromedriver',options=chrome_opt)

            writeLog("------------------浏览器已启动----------------------")

            for user_data_line in user_data_lines:                      # 帮每一个用户打卡
                # 用户信息（去除末尾的\n）
                user_data = str(user_data_line).strip()
                login_data = json.loads(user_data)

                user = login_data['username']
                pw = login_data['password']
                email = login_data['email_address']
                destination = login_data['destination']
                name = login_data['name']
                # 博士生入校申请有可能需要手机号
                phone = login_data['phone']
                hold_on = login_data['hold_on']

                if hold_on == "False":
                    enterCampusRequist = False
                    # if len(destination) > 1:
                    #     enterCampusRequist = True
                    #     enter_campus_num = enter_campus_num + enterCampusRequist
                    # else:
                    #     enterCampusRequist = False
                    try:
                        # 登录打卡界面
                        if login(user, pw, login_url, browser):
                            daily_done = checkIn(user, name, browser)
                            if daily_done is True:
                                mail_msg = "<p>Hi [" + user + "], </p>"
                                mail_msg += mailMsg(user, "已成功打卡")
                                if enterCampusRequist is True:
                                    enterCampus(user, pw, name,
                                                destination, phone, browser)
                                    enterCampusDone = checkEnterCampus(browser)
                                    if enterCampusDone is True:  # 再确认一次，以免学校改版导致程序出错
                                        writeLog("再次确认：第二日入校已申请")
                                        mail_msg += mailMsg(user, "第二日入校已申请")
                                        complete_enter_campus_num = complete_enter_campus_num + enterCampusDone
                                    else:
                                        writeLog("再次确认：本次未成功申请第二日入校")
                                        mail_msg += mailMsg(user,
                                                            "本次未成功申请第二日入校")
                                        error_user_data_lines.append(user_data)
                            elif (daily_done == "无法点击提交按钮"):
                                writeLog("用户信息填写不规范")
                                daily_done = False

                            else:
                                error_user_data_lines.append(user_data)

                            # # 发送打卡信息邮件
                            # if len(email) > 1:
                            #     sendMail(mail_msg, email)

                            browser = logout(browser)
                            writeLog(
                                "------------------用户已登出----------------------")

                        else:
                            writeLog(user + name + "：账号密码错误")
                            writeLog(
                                "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                            error_user_data_lines.append(user_data)
                            daily_done = False

                        complete_user_num = complete_user_num + daily_done

                    except Exception as r:  # 当打卡出现未知错误时记录信息
                        error_user_data_lines.append(user_data)
                        writeLog("未知错误 %s" % (r))

                        # 出现未知错误一律重启浏览器
                        browser.quit()
                        time.sleep(2)
                        browser = webdriver.Chrome(
                            executable_path=file_executable_path, options=chrome_opt)
                        continue

                else:
                    hold_on_user_num += 1

            browser.quit()

            while error_user_data_lines:                                  # 当存在未成功打卡的用户，则重新帮助其打卡
                browser = webdriver.Chrome(
                    executable_path=file_executable_path, options=chrome_opt)
                writeLog("------------------浏览器已启动----------------------")

                proccesing_error_user_data_lines = error_user_data_lines  # 正在处理的未成功打卡的用户信息
                # 将未成功打卡的用户信息置空，为了能够继续循环下去
                error_user_data_lines = []

                for proccesing_error_user_data in proccesing_error_user_data_lines:
                    user_data = proccesing_error_user_data
                    login_data = json.loads(proccesing_error_user_data)

                    user = login_data['username']
                    pw = login_data['password']
                    email = login_data['email_address']
                    destination = login_data['destination']
                    name = login_data['name']
                    phone = login_data['phone']

                    try:
                        # 登录打卡界面
                        if login(user, pw, login_url, browser):
                            daily_done = checkIn(user, name, browser)
                            if daily_done is True:
                                mail_msg = "<p>Hi [" + user + "], </p>"
                                mail_msg += mailMsg(user, "已成功打卡")
                                if enterCampusRequist is True:
                                    enterCampus(user, pw, name,
                                                destination, phone, browser)
                                    enterCampusDone = checkEnterCampus(browser)
                                    if enterCampusDone is True:  # 再确认一次，以免学校改版导致程序出错
                                        writeLog("再次确认：第二日入校已申请")
                                        mail_msg += mailMsg(user, "第二日入校已申请")
                                        complete_enter_campus_num = complete_enter_campus_num + enterCampusDone
                                    else:
                                        writeLog("再次确认：本次未成功申请第二日入校")
                                        mail_msg += mailMsg(user,
                                                            "本次未成功申请第二日入校")
                                        error_user_data_lines.append(user_data)
                            else:
                                error_user_data_lines.append(user_data)

                            # 发送打卡信息邮件
                            # if len(email) > 1:
                            #     sendMail(mail_msg, email)

                            browser = logout(browser)
                            writeLog(
                                "------------------用户已登出----------------------")

                        else:
                            writeLog(user + name + "：账号密码错误")
                            writeLog(
                                "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                            daily_done = False

                        complete_user_num = complete_user_num + daily_done

                    except Exception as r:  # 当打卡出现未知错误时记录信息
                        error_user_data_lines.append(user_data)
                        writeLog("未知错误 %s" % (r))

                        # 出现未知错误一律重启浏览器
                        browser.quit()
                        time.sleep(2)
                        browser = webdriver.Chrome(
                            executable_path=file_executable_path, options=chrome_opt)
                        continue

                browser.quit()
                writeLog("------------------浏览器已关闭----------------------")
                time.sleep(5)

            writeLog("今日已完成打卡人数：" + str(complete_user_num) +
                     "(" + str(user_num) + "-" + str(hold_on_user_num) + "=" + str(user_num-hold_on_user_num) + ")")
            mail_msg = "今日已完成打卡人数：" + str(complete_user_num) + "(" + str(user_num) + "-" + str(
                hold_on_user_num) + "=" + str(user_num-hold_on_user_num) + ")\n"
            # writeLog("今日已完成申请第二日入校人数：" + str(complete_enter_campus_num) +
            #          "(" + str(enter_campus_num) + ")")
            # mail_msg += "今日已完成申请第二日入校人数：" + \
            #     str(complete_enter_campus_num) + \
            #     "(" + str(enter_campus_num) + ")\n"

            # 发送邮件
            # sendMail(mail_msg, "example@example.com")

            # 当所有成员当天均成功打卡，则关闭浏览器并昏睡到明天
            sleep_time = (set_hour+24-time.localtime(time.time()).tm_hour) * \
                3600 + (set_minite-time.localtime(time.time()).tm_min)*60
            writeLog("下次打卡开始时间：明天" + str(set_hour) + ':' +
                     str(set_minite) + "，" + "即" + str(sleep_time) + 's后')
            writeLog("###################################################")
            time.sleep(sleep_time)

        except Exception as r:
            writeLog("未知错误 %s" % (r))
            time.sleep(10)  # 昏睡10s
