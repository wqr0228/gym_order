import requests
import easyocr
from PIL import Image
from io import BytesIO
import re
from sys import exit as sys_exit
from lxml import etree
from os import path as os_path, getenv
from getpass import getpass
import time
import datetime

login_url = 'https://elife.fudan.edu.cn/login.jsp'
logout_url = 'https://elife.fudan.edu.cn/logout.jsp'
order_times = ['08:00', '11:00', '12:00', '19:00', '20:00', '21:00']  # 想要预约的时间段 会[按照顺序]依次尝试预约每个时间段的场次，顺序很重要
max_order_num = 2
skip_days = 1


class Elife():
    '''
    校园生活服务平台
    预约前后进行登入/登出
    '''
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36"

    def __init__(self,
                 uid, passwd, mobile,
                 url_login='https://uis.fudan.edu.cn/authserver/login?service=https%3A%2F%2Felife.fudan.edu.cn%2Flogin2.action',
                 url_code='https://elife.fudan.edu.cn/image.jsp'):
        self.uid = uid
        self.passwd = passwd
        self.mobile = mobile
        self.url_login = url_login
        self.url_code = url_code

        self.session = requests.Session()
        self.session.keep_alive = True  # 改为持久连接
        self.session.headers['User-Agent'] = self.UA

    def _page_init(self):
        """
        检查是否能打开登录页面
        :return: 登录页page source
        """
        print("◉ Initiating——", end='')
        page_login = self.session.get(self.url_login)

        print("return status code",
              page_login.status_code)

        if page_login.status_code == 200:
            print("◉ Initiated——", end="")
            return page_login.text
        else:
            print("◉ Fail to open Login Page, Check your Internet connection\n")
            self.close()

    def login(self):
        """
        登录elife，获取cookies
        """
        page_login = self._page_init()

        print("getting tokens")
        data = {
            "username": self.uid,
            "password": self.passwd,
            "service": "https://elife.fudan.edu.cn/login2.action"
        }

        # 获取登录页上的令牌
        result = re.findall(
            '<input type="hidden" name="([a-zA-Z0-9\-_]+)" value="([a-zA-Z0-9\-_]+)"/?>', page_login)
        # print(result)
        # result 是一个列表，列表中的每一项是包含 name 和 value 的 tuple，例如
        # [('lt', 'LT-6711210-Ia3WttcMvLBWNBygRNHdNzHzB49jlQ1602983174755-7xmC-cas'), ('dllt', 'userNamePasswordLogin'), ('execution', 'e1s1'), ('_eventId', 'submit'), ('rmShown', '1')]
        data.update(result)

        headers = {
            "Host": "uis.fudan.edu.cn",
            "Origin": "https://uis.fudan.edu.cn",
            "Referer": self.url_login,
            "User-Agent": self.UA
        }

        print("◉ Login ing——", end="")
        post = self.session.post(
            self.url_login,
            data=data,
            headers=headers,
            allow_redirects=False)
        url_redirect = post.url

        print("return status code", post.status_code)

        get = self.session.get(
            url_redirect
        )
        # print(get.status_code)
        # print(get.url)
        # print(self.session.cookies.items())

        if get.status_code == 200:
            print("\n***********************"
                  "\n◉ elife首页登录成功"
                  "\n***********************\n")
        else:
            print("◉ 登录失败，请检查账号信息")
            self.close()

    def logout(self):
        """
        执行登出
        """
        exit_url = 'https://elife.fudan.edu.cn/j_spring_security_logout'
        expire = self.session.get(exit_url, allow_redirects=False).headers.get('set-cookie')
        # print(expire)
        
        print("\n*******今日已预约*******")
        if '01-Jan-1970' in expire:
            print("◉ 登出完毕")
        else:
            print("◉ 登出异常")

    def close(self, exit_code=0):
        """
        执行登出并关闭会话
        """
        self.logout()
        self.session.close()
        print("◉ 关闭会话")
        print("************************")
        sys_exit(exit_code)

    def order(self):
        '''
        预约场地，包括多次预约
        '''
        print("\n***********************"
              "\n◉ 开始预约"
              "\n***********************")
        date = (datetime.date.today() + datetime.timedelta(days=skip_days)).strftime("%Y-%m-%d")
        # url_court = 'https://elife.fudan.edu.cn/public/front/getResource2.htm?contentId=8aecc6ce749544fd01749a31a04332c2&ordersId=&currentDate=' #江湾体育馆羽毛球场
        url_court = 'https://elife.fudan.edu.cn/public/front/getResource2.htm?contentId=2c9c486e4f821a19014f82418a900004&ordersId=&currentDate='  # 正大体育馆羽毛球场
        url_date = url_court + date
        success_times = 0
        for i, str in enumerate(order_times):
            print("\n◉ 第{}次尝试 时段：{}".format(i+1, str))
            success_flag = self._order_once(url_date, str)
            if success_flag:
                success_times += 1
            if success_times >= max_order_num:
                break

        print('\n全部预约完成！')

    def _order_once(self, url, time_str):
        '''
        执行一次预约
        '''
        page_date = self.session.get(url)  # 要预约的当天场次选择页面
        page_date_html = etree.HTML(page_date.text)
        order_btn_list = page_date_html.xpath('//tr[td/font/text()="{}"]/td/img/@onclick'.format(time_str))
        # 是一个预约时间的按钮onclick属性list，形如["checkUser('8aecc6ce7fb5f264017fbedaf2ac7d87',this)"]，若该时间段能预约则应该有onclick属性，若按钮为灰则无onclick属性
        if len(order_btn_list) == 0:  # 没有onclick属性，说明该时间段不能预约
            print('当前时段不可预约！')
            return False

        resource_ids = order_btn_list[0][11:-7]
        service_content_id = page_date_html.xpath('//input[@name="serviceContent.id"]/@value')[0]  # ['2c9c486e4f821a19014f82418a900004']
        service_category_id = page_date_html.xpath('//input[@name="serviceCategory.id"]/@value')[0]   # ['2c9c486e4f821a19014f82381feb0001']
        if len(page_date_html.xpath('//input[@name="codeStr"]/@value')) == 0:
            code_str = ''
        else:
            code_str = page_date_html.xpath('//input[@name="codeStr"]/@value')[0]
        params = {
            'serviceContent.id': service_content_id,
            'serviceCategory.id': service_category_id,
            'codeStr': code_str,
            'resourceIds': resource_ids,
            'orderCounts': 1
        }
        page_order = self.session.get('https://elife.fudan.edu.cn/public/front/loadOrderForm_ordinary.htm', params=params)  # 获取预定页面
        page_order_html = etree.HTML(page_order.text)
        order_user = page_order_html.xpath('//*[@id="order_user"]/@value')[0]  # 用户名
        code = self._read_captcha()
        print('验证码：', code)

        self.session.headers.update({'referer': url})
        files = {'serviceContent.id': (None, service_content_id),
                 'serviceCategory.id':  (None, service_category_id),
                 'contentChild': (None, ''),
                 'codeStr': (None, code_str),
                 'itemsPrice': (None, ''),
                 'acceptPrice': (None, ''),
                 'orderuser': (None, order_user),
                 'resourceIds': (None, resource_ids),
                 'orderCounts': (None, 1),
                 'lastDays': (None, 0),
                 'mobile': (None, self.mobile),
                 'imageCodeName': (None, code),
                 'd_cgyy.bz': (None, '')}
        order_result = self.session.post('https://elife.fudan.edu.cn/public/front/saveOrder.htm?op=order', files=files, allow_redirects=True)  # 如果预约成功会自动重定向到操作成功页面
        if order_result.url.find('%E6%93%8D%E4%BD%9C%E6%88%90%E5%8A%9F') >= 0:  # url编码中含有“操作成功”，即表示预约成功，否则打印失败信息
            print('预约成功！')
            return True
        else:
            print('预约失败！')
            print('URL:', order_result.url)
            # print(order_result.text)
            return False

    def _read_captcha(self):
        '''
        读取验证码，如果错误则重新获取，直到成功识别出4个数字的验证码
        '''
        while True:  # 验证码识别为空或者不是4个字符，则重试
            img_code = Image.open(BytesIO(self.session.get(self.url_code).content))
            # img_code.show()
            reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            result = reader.readtext(img_code)
            if len(result) > 0 and len(result[0][1].replace(' ', '')) == 4:
                break
            else:
                print('验证码识别错误，重试...')
        return result[0][1]


def get_account():
    """
    获取账号信息
    """
    uid = getenv("STD_ID")
    psw = getenv("PASSWORD")
    mobile = getenv("MOBILE")
    if uid != None and psw != None:
        print("从环境变量中获取了用户名和密码！")
        return uid, psw, mobile
    print("\n\n请仔细阅读以下日志！！\n请仔细阅读以下日志！！！！\n请仔细阅读以下日志！！！！！！\n\n")
    if os_path.exists("account.txt"):
        print("读取账号中……")
        with open("account.txt", "r") as old:
            raw = old.readlines()
        if (raw[0][:3] != "uid") or (len(raw[0]) < 10):
            print("account.txt 内容无效, 请手动修改内容")
            sys_exit()
        uid = (raw[0].split(":"))[1].strip()
        psw = (raw[1].split(":"))[1].strip()
        mobile = (raw[2].split(":"))[1].strip()

    else:
        print("未找到account.txt, 判断为首次运行, 请接下来依次输入学号、密码、电话")
        uid = input("学号：")
        psw = getpass("密码：")
        mobile = input("电话：")
        with open("account.txt", "w") as new:
            tmp = "uid:" + uid + "\npsw:" + psw +\
                "\n\n\n以上两行冒号后分别写上学号密码，不要加空格/换行，谢谢\n\n请注意文件安全，不要放在明显位置\n\n可以从dailyFudan.exe创建快捷方式到桌面"
            new.write(tmp)
        print("账号已保存在目录下account.txt，请注意文件安全，不要放在明显位置\n\n建议拉个快捷方式到桌面")

    return uid, psw, mobile


if __name__ == '__main__':
    uid, passwd, mobile = get_account()
    e = Elife(uid, passwd, mobile)
    e.login()
    e.order()
    e.close()
