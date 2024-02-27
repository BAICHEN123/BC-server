#!/usr/bin/python3
# -*- coding: utf-8 -*-
import smtplib
import MyPrintE
import threading
import time
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import os
import MyConfig

HOST = MyConfig.EMAIL_HOST
# SUBJECT ='何辰川的APP'
FROM = MyConfig.EMAIL_FROM
str_email_password = ""
if MyConfig.EMAIL_STR_EMAIL_PASSWORD:
    str_email_password = MyConfig.EMAIL_STR_EMAIL_PASSWORD
PORT = MyConfig.EMAIL_PORT
conect_lock = threading.Lock()

__str_email_password_file_name = MyConfig.EMAIL_PASSWORD_FILE_NAME


def get_str_email_password():
    global str_email_password
    return str_email_password


def load_email_password(file_name=__str_email_password_file_name):
    global str_email_password
    try:
        f = open(file_name, "r")
    except FileNotFoundError as e:
        f = open(file_name, "w")
        f.write("文件不存在，但是我创建了一个\n")
        f.close()
        return 0
    str_data = f.read()
    f.close()
    str_data = str_data.strip()
    if type(str_data) == str and len(str_data) > 0:
        str_email_password = str_data
        return len(str_data)


def init_email_passwd(file_name=__str_email_password_file_name):
    if os.path.isfile(file_name):
        load_email_password()


def send_email_yanzhenma(str_email, data):
    data = "[验证码][" + data + "]五分钟内有效"
    email_send_str(str_email, data)  # 发送时间的MD5前4位做验证码


def send_email_warning(
    str_to_email, str_u_name, str_e_name, str_message, SUBJECT="何辰川的APP"
):
    str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    str_data = f"""<html><body>
	<div>【{str_u_name}】您好，您的【{str_e_name}】在【{str_time}】收到警告。</div>
	<table border="1">
	{str_message}
	</table>
	<div>相同错误邮件一小时提醒一次，暂时无法修改 </div>
	</body></html>"""
    return email_send_html(str_to_email, str_data, SUBJECT)


def email_send_str(str_to_email, str_data, SUBJECT="何辰川的APP"):
    message = MIMEText(str_data)
    message["From"] = FROM
    message["To"] = str_to_email
    message["Subject"] = SUBJECT
    return email_send(str_to_email, message, SUBJECT)


def email_send_html(str_to_email, str_data, SUBJECT="何辰川的APP"):
    message = MIMEText(str_data, "html", "utf-8")
    message["From"] = FROM
    message["To"] = str_to_email
    message["Subject"] = SUBJECT
    return email_send(str_to_email, message, SUBJECT)


def email_send_lock(str_to_email, message, SUBJECT="何辰川的APP"):
    assert type(message) == MIMEText
    i = 3
    email_client = None
    while i > 0 and email_client == None:
        i = i - 1
        email_client = get_email_conect()

    if email_client:
        try:
            end1 = email_client.sendmail(FROM, str_to_email, message.as_string())
            email_client.quit()
            print("邮件发送成功", end1)
            return 1
        except smtplib.SMTPException as e:
            MyPrintE.e_print(e, "Error: 无法发送邮件")
            return 0
    else:
        print("发送邮件身份验证出现问题")
        return 2


class thread_send_email_2(threading.Thread):
    # 开个子线程发邮箱验证码，不然这里占用时间太多
    def __init__(self1, str_email, data, SUBJECT="何辰川的APP"):
        super().__init__()
        self1.str_email = str_email
        self1.data = data
        self1.SUBJECT = SUBJECT

    def run(self1):
        with conect_lock:
            i = 3
            while email_send_lock(self1.str_email, self1.data, self1.SUBJECT) != 1:
                i = i - 1
                if i < 0:
                    return


def email_send(str_to_email, message, SUBJECT="何辰川的APP"):
    thread_send_email_2(str_to_email, message, SUBJECT).start()


def get_email_conect(host=HOST, port=PORT):
    conect_obj: smtplib.SMTP_SSL = None
    conect_obj = smtplib.SMTP_SSL(host, port)
    conect_obj.connect(host, port)
    i = 0
    while True:
        if i == 3:
            conect_obj = None
            return conect_obj
        try:
            assert i < 3
            result1, result2 = conect_obj.login(FROM, get_str_email_password())
            if result2 == b"Authentication successful":
                break
            else:
                i = i + 1
                print("Error: smtplib login result2")
                time.sleep(1)
        except smtplib.SMTPAuthenticationError:
            i = i + 1
            print("Error: smtplib.SMTPAuthenticationError")
            time.sleep(1)
        except smtplib.SMTPServerDisconnected:
            i = 3
    return conect_obj
