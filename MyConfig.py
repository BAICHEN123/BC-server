#!/usr/bin/python3
#utf-8
DEBUG = False
if DEBUG:
    HTTP_PORT = 8079
    TCP_PORT = 9997
    UDP_PORT = 9996 
else :
    HTTP_PORT = 8080
    TCP_PORT = 9999
    UDP_PORT = 9998

USER_HEAD_JPG_DIR = "./head"
# 储存用户头像的文件夹

SQL_CHARSET = "utf8mb4"
SQL_HOST = "localhost"
SQL_PASSWD = "%^TY56ty"

if DEBUG: 
    SQL_USER = "user_test1"
    SQL_DATABASE = "test1"
else:
    SQL_USER = "user_bc_server"
    SQL_DATABASE = "bc_server"

SQL_AUTH_PLUGIN = "mysql_native_password"
SQL_ERROR_EMAIL = "2280057905@qq.com"


EMAIL_HOST = "smtp.qq.com" 
EMAIL_FROM = "2280057905@qq.com"
EMAIL_STR_EMAIL_PASSWORD = "ztyhzosrkgkzdiif"
EMAIL_PORT = 465 
EMAIL_PASSWORD_FILE_NAME = "./email_password.txt" 
# EMAIL_STR_EMAIL_PASSWORD EMAIL_PASSWORD_FILE_NAME 至少有一个有效，不然不能发邮件


OTA_DIR_NAME = "./OTAFile"
# 储存 OTA 固件的文件夹

BLACKIP_FILE_NAME = "./blackip.txt" 
# 访问 "http://localhost:HTTP_PORT/blackipreload" 可以重新加载 BLACKIP_FILE_NAME  EMAIL_PASSWORD_FILE_NAME的数据