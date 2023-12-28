import os
"""请确保传入的ip是合法ip，此文件不做ip的合法校验"""

__dict_black_ip = dict()  # 储存正在计数的ip
__list_black_ip = dict()  # 储存彻底拉黑的ip
__str_file_name = "blackip.txt"


def __file_read(str_file_name=__str_file_name):
    global __list_black_ip
    f = open(str_file_name, "r")
    for item in f.readlines():
        __list_black_ip[item[:-1]] = None
        # __list_black_ip.append(item[:-1])
    f.close()


def __file_save(str_ip, str_file_name=__str_file_name):
    f = open(str_file_name, "a")
    f.write(str_ip + "\n")
    f.close()
    pass


# 判断是否是黑名单ip
def is_black_ip(str_ip):
    global __list_black_ip
    if str_ip in __list_black_ip:
        return True
    return False


# 希望将此ip拉黑
def add_black_ip(str_ip):
    global __dict_black_ip, __list_black_ip
    try:
        __dict_black_ip[str_ip] = __dict_black_ip[str_ip] + 1
        if __dict_black_ip[str_ip] == 2:
            __file_save(str_ip)
            __list_black_ip[str_ip] = None
            __dict_black_ip.pop(str_ip)
        return
    except KeyError:
        __dict_black_ip[str_ip] = 0
        return


# 初始化，重新加载文件，都是调用这个函数
def black_ip_init(str_file_name=__str_file_name):
    global __dict_black_ip, __list_black_ip
    __dict_black_ip = dict()  # 储存正在计数的ip
    __list_black_ip = dict()  # 储存彻底拉黑的ip
    if os.path.isfile(str_file_name):
        __file_read(str_file_name)
    return len(__list_black_ip)
